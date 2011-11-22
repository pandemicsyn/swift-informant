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

from webob import Request, Response
from swift.common.utils import get_logger
from eventlet.green import socket
from random import random


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

    def send_event(self, payload):
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.sendto(payload, self.statsd_addr)
        except Exception:
            #udp sendto failed (socket already in use?), but thats ok
            self.logger.exception(_("Error trying to send statsd event"))

    def statsd_counter_increment(self, stats, delta=1):
        """
        Increment multiple statsd stats counters
        """
        if self.statsd_sample_rate < 1:
            if random() <= self.statsd_sample_rate:
                for item in stats:
                    payload = "%s:%s|c|@%s" % (item, delta,
                        self.statsd_sample_rate)
                    self.send_event(payload)
        else:
            for item in stats:
                payload = "%s:%s|c" % (item, delta)
                self.send_event(payload)

    def statsd_event(self, env, req):
        #wrapping the *whole thing* incase something bad happens
        #better safe then sorry ?
        try:
            response = getattr(req, 'response', None)
            if not response:
                #no response but we can still fire the event for the method.
                self.statsd_counter_increment([req.method])
            else:
                status_int = response.status_int
                if getattr(req, 'client_disconnect', False) or \
                        getattr(response, 'client_disconnect', False):
                    status_int = 499
                if req.path.count('/') is 2:
                    request_event = "acct.%s" % req.method
                    status_event = "acct.%d" % status_int
                elif req.path.count('/') is 3:
                    request_event = "cont.%s" % req.method
                    status_event = "cont.%d" % status_int
                elif req.path.count('/') >= 4:
                    request_event = "obj.%s" % req.method
                    status_event = "obj.%d" % status_int
                else:
                    request_event = "invalid.%s" % req.method
                    status_event = "invalid.%d" % status_int
                self.statsd_counter_increment([request_event, status_event])
        except Exception:
            try:
                self.logger.exception(_("Encountered error in statsd_event"))
            except Exception:
                pass

    def __call__(self, env, start_response):
        req = Request(env)
        if 'eventlet.posthooks' in env:
            env['eventlet.posthooks'].append(
                (self.statsd_event, (req,), {}))
            return self.app(env, start_response)
        else:
            # No posthook support better to just not gen events
            return self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def informant_filter(app):
        return Informant(app, conf)
    return informant_filter
