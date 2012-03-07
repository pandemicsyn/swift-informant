# Copyright (c) 2010-2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from webob import Request
from swift.common.utils import get_logger, TRUE_VALUES
from eventlet.green import socket
from sys import maxint
from time import time


class Informant(object):
    """
    Informant Middleware used for sending events to statsd
    """
    def __init__(self, app, conf, *args, **kwargs):
        self.app = app
        self.logger = get_logger(conf, log_route='informant')
        self.statsd_host = conf.get('statsd_host', '127.0.0.1')
        self.statsd_port = int(conf.get('statsd_port', '8125'))
        self.statsd_addr = (self.statsd_host, self.statsd_port)
        self.statsd_sample_rate = float(conf.get('statsd_sample_rate', '.5'))
        self.valid_methods = conf.get('valid_http_methods',
                                        'GET,HEAD,POST,PUT,DELETE,COPY')
        self.valid_methods = [s.strip().upper() for s in \
                                self.valid_methods.split(',')  if s.strip()]
        self.combined_events = conf.get(
                                'combined_events', 'no').lower() in TRUE_VALUES
        self.metric_name_prepend = conf.get('metric_name_prepend', '')
        self.actual_rate = 0.0
        self.counter = 0
        self.monitored = 0

    def _send_events(self, payloads, combined_events=False):
        """Fire the udp events to statsd"""
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if not combined_events:
                for payload in payloads:
                    udp_socket.sendto(payload, self.statsd_addr)
            else:
                #send multiple events per packet
                payload = "#".join(payloads)
                udp_socket.sendto(payload, self.statsd_addr)
        except Exception:
            self.logger.exception(_("Error sending statsd event"))

    def _send_sampled_event(self):
        """"
        Track the sample rate and checks to see if this is a request
        that should be sent to statsd.

        :returns: True if the event should be sent to statsd
        """
        send_sample = False
        self.counter += 1
        if self.actual_rate < self.statsd_sample_rate:
            self.monitored += 1
            send_sample = True
        self.actual_rate = float(self.monitored) / float(self.counter)
        if self.counter >= maxint or self.monitored >= maxint:
            self.counter = 0
            self.monitored = 0
        return send_sample

    def statsd_event(self, env, req):
        """generate a statsd event for this request"""
        try:
            if self._send_sampled_event():
                request_method = req.method.upper()
                if request_method not in self.valid_methods:
                    request_method = "BAD_METHOD"
                if 'informant.status' in env and 'informant.start_time' in env:
                    status_int = env['informant.status']
                    response = getattr(req, 'response', None)
                    if getattr(req, 'client_disconnect', False) or \
                            getattr(response, 'client_disconnect', False):
                        status_int = 499
                    duration = (time() - env['informant.start_time']) * 1000
                    transferred = getattr(req, 'bytes_transferred', 0)
                    if transferred is '-' or transferred is 0:
                        transferred = getattr(response, 'bytes_transferred', 0)
                    if transferred is '-':
                        transferred = 0
                try:
                    stat_type = ['invalid', 'invalid', 'acct', 'cont', 'obj'] \
                                    [req.path.count('/')]
                except IndexError:
                    stat_type = 'obj'
                metric_name = "%s.%s.%s" % (stat_type, request_method, status_int)
                counter = "%s%s:1|c|@%s" % (self.metric_name_prepend, metric_name, 
                                            self.statsd_sample_rate)
                timer = "%s%s:%d|ms|@%s" % (self.metric_name_prepend, metric_name, duration,
                                            self.statsd_sample_rate)
                tfer = "%stfer.%s:%s|c|@%s" % (self.metric_name_prepend, metric_name,
                                               transferred, self.statsd_sample_rate)
                self._send_events([counter, timer, tfer], self.combined_events)
        except Exception:
            try:
                self.logger.exception(_("Encountered error in statsd_event"))
            except Exception:
                pass

    def __call__(self, env, start_response):

        def _start_response(status, headers, exc_info=None):
            """start_response wrapper to add request status to env"""
            env['informant.status'] = int(status.split(' ', 1)[0])
            start_response(status, headers, exc_info)

        req = Request(env)
        try:
            if 'eventlet.posthooks' in env:
                env['informant.start_time'] = time()
                env['eventlet.posthooks'].append(
                    (self.statsd_event, (req,), {}))
            return self.app(env, _start_response)
        except Exception:
            self.logger.exception('WSGI EXCEPTION:')
            _start_response('500 Internal Server Error',
                            [('Content-Length', '0')])
            return []


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def informant_filter(app):
        return Informant(app, conf)
    return informant_filter
