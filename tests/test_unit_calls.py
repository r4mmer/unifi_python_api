import sys
import unittest
import json

import requests
import urllib3
import trafaret as t

from unifi_api import UnifiClient
from unifi_api.base_api import AbstractUnifiSession
from unifi_api.utils import models
from unifi_api.utils.decorators import requires_login, call_requires_login


class BaseTestCase(unittest.TestCase):
    def assertNotRaises(self, ex_cls, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except ex_cls as ex:
            self.fail(ex)

    def setup_output_test(self):
        from io import StringIO
        self.saved_stdout = sys.stdout
        self.cout = StringIO()
        sys.stdout = self.cout

    def finish_output_test(self):
        sys.stdout = self.saved_stdout

    def get_cout(self):
        # using StringIO
        ret = self.cout.getvalue().strip()
        self.cout.truncate(0)
        self.cout.seek(0)
        return ret


class TAbstractUnifiSession(AbstractUnifiSession):
    def login(self, username=None, password=None):
        return True
    def logout(self, username=None, password=None):
        return not self.logged_in


class TestAbstractUnifiSession(BaseTestCase):

    def test_init_missing_params(self):
        self.assertRaises(t.DataError, AbstractUnifiSession)

    def test_init_param_base_url(self):
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "http://example.com")
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "http://example.com:8443")
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com")
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443")

        self.assertRaises(t.DataError, AbstractUnifiSession, 123)
        self.assertRaises(t.DataError, AbstractUnifiSession, "")
        self.assertRaises(t.DataError, AbstractUnifiSession, "blablabla")

    def test_init_param_verify(self):
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", ssl_verify=True)
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", ssl_verify=False)

        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", ssl_verify='123')
        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", ssl_verify=123)
        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", ssl_verify={'foo':'bar'})

    def test_init_param_debug(self):
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", debug=True)
        self.assertNotRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", debug=False)

        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", debug='123')
        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", debug=123)
        self.assertRaises(t.DataError, AbstractUnifiSession, "https://example.com:8443", debug={'foo':'bar'})


    def test_init_param_credentials(self):
        self.assertNotRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", username="aaa", password="aaa")
        self.assertNotRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", username="aaa")
        self.assertNotRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", password="aaa")

        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", username=123)
        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", username=True)
        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", username={'foo':'bar'})
        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", password=123)
        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", password=True)
        self.assertRaises(t.DataError, TAbstractUnifiSession, "https://example.com:8443", password={'foo':'bar'})

    def test_debug(self):
        # setup catch stdout
        self.setup_output_test()
        # setup test
        instance = AbstractUnifiSession("https://example.com:8443", debug=True)

        instance.debug("123")
        outp1 = self.get_cout()
        self.assertEqual(outp1, "123")

        instance = AbstractUnifiSession("https://example.com:8443", debug=False)
        instance.debug("aaa")
        outp2 = self.get_cout()
        self.assertEqual(outp2, "")
        # free stdout
        self.finish_output_test()

    def test_endpoint(self):
        instance = AbstractUnifiSession("https://example.com")
        self.assertEqual("https://example.com/api/bla/bla", instance.endpoint("/api/bla/bla"))
        self.assertEqual("https://example.com/api/bla/bla", instance.endpoint("api/bla/bla"))
        # other endpoints

    def test_process_response(self):
        def make_response(method, url, body=json.dumps({}), headers={}, status=200):
            from io import BytesIO
            req = requests.Request(method.upper(), url).prepare()
            body_stream = BytesIO(body) if isinstance(body, bytes) else BytesIO(body.encode())
            headers = urllib3.response.HTTPHeaderDict(headers)
            resp = urllib3.HTTPResponse(body_stream, headers, status, preload_content=False)
            return requests.adapters.HTTPAdapter().build_response(req, resp)

        instance = AbstractUnifiSession("https://example.com", debug=True)
        self.setup_output_test()
        resp_not_json_header = make_response('POST', 'https://example.com')
        resp_not_json_body = make_response('POST', 'https://example.com', headers={'content-type': 'application/json'})
        data_ok = {'data': ['123'], 'meta': {'rc': 'ok', 'msg': 'aaa'}}
        resp_ok = make_response('POST', 'https://example.com', body=json.dumps(data_ok), headers={'content-type': 'application/json'})
        data_error = {'data': ['123'], 'meta': {'rc': 'error', 'msg': 'aaa'}}
        resp_error = make_response('POST', 'https://example.com', body=json.dumps(data_error), headers={'content-type': 'application/json'})

        with self.assertRaises(ValueError) as ctx:
            instance.process_response(resp_not_json_header)
        self.assertEqual('Content type should be json', str(ctx.exception))
        with self.assertRaises(t.DataError) as ctx:
            instance.process_response(resp_not_json_body)
        # Boolean error
        self.assertEqual(True, instance.process_response(resp_ok, boolean=True))
        self.assertEqual(False, instance.process_response(resp_error, boolean=True))

        self.get_cout()
        instance.process_response(resp_error)
        outp = self.get_cout()
        self.assertEqual('aaa', outp)

        self.assertEqual(['123'], instance.process_response(resp_ok))

        self.finish_output_test()

# models: ...
class TestModels(BaseTestCase):
    def test_ident(self):
        self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
