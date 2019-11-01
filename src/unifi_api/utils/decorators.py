# custom decorators
from functools import wraps

import trafaret as t

from .exceptions import UnifiLoginError
from .models import JsonResponse

def call_requires_login(func):
    def validate(resp):
        if resp.status_code == 401 and 'application/json' in resp.headers.get('Content-Type'):
            d = JsonResponse.check(resp.json())
            if d['meta']['msg'] == 'api.err.LoginRequired':
                return
        return resp

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from ..base_api import AbstractUnifiSession
        assert isinstance(self, AbstractUnifiSession), 'Calls must be made from an AbstractUnifiSession subclass'
        r = None
        for i in range(3):
            r = func(self, *args, **kwargs)
            if validate(r) is not None:
                break
            self.debug('*****needs to reconnect to controller')
            self.clear_cookies()
            self.login()
        else:
            raise UnifiLoginError('Reconnection to controller failed')
        return r
    return wrapper


def requires_login(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from ..base_api import AbstractUnifiSession
        assert isinstance(self, AbstractUnifiSession), 'Must be called from an AbstractUnifiSession subclass'
        # could try sometimes to ease bad connection cases
        if not self.logged_in:
            self.login()
        return func(self, *args, **kwargs)
    return wrapper

def guard(params=None, **kwargs):
    specs = t.Forward()
    if params is None:
        specs << t.Dict(**kwargs)
    else:
        specs << params
    def wrapped(fn):
        guarder = t.guard(specs)
        wrapper = wraps(fn)(guarder(fn))
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return wrapped
