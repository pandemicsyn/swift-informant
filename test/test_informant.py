import unittest

from webob import Request, Response
from informant import middleware

class FakeApp(object):
    
    def __init__(self, status_headers_body_iter=None):
        self.calls = 0
        self.status_headers_body_iter = status_headers_body_iter
        if not self.status_headers_body_iter:
            self.status_headers_body_iter = iter([('404 Not Found', {
                'x-test-header-one-a': 'value1',
                'x-test-header-two-a': 'value2',
                'x-test-header-two-b': 'value3'}, '')])
        self.request = None
    
    def __call__(self, env, start_response):
        self.calls += 1
        self.request = Request.blank('', environ=env)
        status, headers, body = self.status_headers_body_iter.next()
        return Response(status=status, headers=headers,
                        body=body)(env, start_response)

def start_response(*args):
    pass

class Mocked(object):
    
    def __init__(self):
        self._send_events_calls = []
        
    def fake_send_events(self, *args, **kwargs):
        self._send_events_calls = [((args, kwargs))]
    
    def fake_send_sampled_event(self, *args, **kwargs):
        return True
        
    def fake_time(self, *args, **kwargs):
        return 1331098500.00

class TestInformant(unittest.TestCase):

    def setUp(self):
        self.mock = Mocked()
        self.app = middleware.Informant(FakeApp(), {})
        self.orig_send_events = self.app._send_events
        self.orig_send_sampled_event = self.app._send_sampled_event
        self.app._send_events = self.mock.fake_send_events
        self.app._send_sampled_event = self.mock.fake_send_sampled_event

    def tearDown(self):
        self.app._send_events = self.orig_send_events
        self.app._send_sampled_event = self.orig_send_sampled_event

    def test_informant_invalid(self):
        expected = [((['invalid.GET.200:1|c|@0.5', 'invalid.GET.200:1331097138625|ms|@0.5', 'tfer.invalid.GET.200:0|c|@0.5']))]
        req = Request.blank('/invalidrandomness', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        self.assertEquals(counter.startswith('invalid.GET.200'), True)
        self.assertEquals(timer.startswith('invalid.GET.200'), True)
        self.assertEquals(tfer.startswith('tfer.invalid.GET.200'), True)

    def test_informant_bad_method(self):
        req = Request.blank('/invalidrandomness', environ={'REQUEST_METHOD': 'WTFMONKEYS'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('invalid.BAD_METHOD.200'), True)
        self.assertEquals(timer.startswith('invalid.BAD_METHOD.200'), True)
        self.assertEquals(tfer.startswith('tfer.invalid.BAD_METHOD.200'), True)
        
    def test_informant_client_disconnect(self):
        req = Request.blank('/invalidrandomness', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = True
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('invalid.GET.499'), True)
        self.assertEquals(timer.startswith('invalid.GET.499'), True)
        self.assertEquals(tfer.startswith('tfer.invalid.GET.499'), True)
        
    def test_informant_empty_transferred(self):
        req = Request.blank('/invalidrandomness', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "-"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(tfer.startswith('tfer.invalid.GET.200:0'), True)
    
    def test_informant_acct_op(self):
        req = Request.blank('/v1/someaccount', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('acct.GET.200'), True)
        self.assertEquals(timer.startswith('acct.GET.200'), True)
        self.assertEquals(tfer.startswith('tfer.acct.GET.200:500'), True)
        
    def test_informant_container_op(self):
        req = Request.blank('/v1/someaccount/somecontainer', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('cont.GET.200'), True)
        self.assertEquals(timer.startswith('cont.GET.200'), True)
        self.assertEquals(tfer.startswith('tfer.cont.GET.200:500'), True)
        
    def test_informant_object_op(self):
        req = Request.blank('/v1/someaccount/somecontainer/someobj', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('obj.GET.200'), True)
        self.assertEquals(timer.startswith('obj.GET.200'), True)
        self.assertEquals(tfer.startswith('tfer.obj.GET.200:500'), True)
    
    def test_informant_pseudodirs(self):
        req = Request.blank('/v1/theact/thecont/theobj/with/extras', environ={'REQUEST_METHOD': 'GET'})
        req.environ['informant.status'] = 200
        req.environ['informant.start_time'] = 1331098000.00
        req.client_disconnect = False
        req.bytes_transferred = "500"
        print "--> %s" % req.environ
        resp = self.app.statsd_event(req.environ, req)
        counter = self.mock._send_events_calls[0][0][0][0]
        timer = self.mock._send_events_calls[0][0][0][1]
        tfer = self.mock._send_events_calls[0][0][0][2]
        print self.mock._send_events_calls
        self.assertEquals(counter.startswith('obj.GET.200'), True)
        self.assertEquals(timer.startswith('obj.GET.200'), True)
        self.assertEquals(tfer.startswith('tfer.obj.GET.200:500'), True)
        
    def test_informant_methods(self):
        for method in ['GET', 'HEAD', 'PUT', 'POST', 'DELETE', '-JUNK']:
            req = Request.blank('/v1/someaccount', environ={'REQUEST_METHOD': method})
            req.environ['informant.status'] = 200
            req.environ['informant.start_time'] = 1331098000.00
            req.client_disconnect = False
            req.bytes_transferred = "500"
            print "--> %s" % req.environ
            resp = self.app.statsd_event(req.environ, req)
            counter = self.mock._send_events_calls[0][0][0][0]
            timer = self.mock._send_events_calls[0][0][0][1]
            tfer = self.mock._send_events_calls[0][0][0][2]
            print self.mock._send_events_calls
            if method is not '-JUNK':
                self.assertEquals(counter.startswith('acct.%s.200' % method), True)
                self.assertEquals(timer.startswith('acct.%s.200' % method), True)
                self.assertEquals(tfer.startswith('tfer.acct.%s.200:500' % method), True)
            else:
                self.assertEquals(counter.startswith('acct.BAD_METHOD.200'), True)
                self.assertEquals(timer.startswith('acct.BAD_METHOD.200'), True)
                self.assertEquals(tfer.startswith('tfer.acct.BAD_METHOD.200:500'), True)   


if __name__ == '__main__':
    unittest.main()
