from urllib.parse import urljoin

import requests

from .utils import models
from .utils.decorators import call_requires_login, requires_login, guard


class AbstractUnifiSession:
    @guard(models.init_params)
    def __init__(self, base_url, ssl_verify=False, debug=False, username=None, password=None):
        # set init params
        self.base_url = base_url
        self.ssl_verify = ssl_verify
        self._debug = debug
        self.username = username
        self.password = password

        # init session
        self.clean_session()

    @requires_login
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return

    def debug(self, *args, **kwargs):
        # TODO: change for logging
        if self._debug:
            print(*args, **kwargs)

    def endpoint(self, path):
        return urljoin(self.base_url, path)

    def clear_cookies(self):
        self._session.cookies.clear()

    def clean_session(self):
        if hasattr(self, '_session'):
            self._session.close()
        self._session = requests.session()
        self._session.verify = self.ssl_verify

    def close_session(self):
        self._session.close()

    @property
    def session(self):
        return self._session

    @property
    def logged_in(self):
        return 'unifises' in self.session.cookies

    @call_requires_login
    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    @call_requires_login
    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    @call_requires_login
    def put(self, *args, **kwargs):
        return self.session.put(*args, **kwargs)

    @call_requires_login
    def delete(self, *args, **kwargs):
        return self.session.delete(*args, **kwargs)

    def process_response(self, response, boolean=False):
        if 'Content-Type' not in response.headers or 'application/json' not in response.headers['Content-Type']:
            # raise or return?
            self.debug(response.status_code)
            self.debug(response.headers)
            self.debug(response.text)
            raise ValueError('Content type should be json')

        data = models.JsonResponse(response.json())
        if data['meta']['rc'] == 'ok':
            return True if boolean else data['data']
        self.debug(data['meta']['msg'])
        return False

    def login(self, username=None, password=None):
        raise NotImplementedError('login')

    def logout(self):
        raise NotImplementedError('logout')
