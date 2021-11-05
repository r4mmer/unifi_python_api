from datetime import datetime
import trafaret as t

from .base_api import AbstractUnifiSession
from .utils import models
from .utils.decorators import requires_login, guard
from .utils.exceptions import UnifiLoginError


class UnifiClient(AbstractUnifiSession):
    '''
        Unifi API client
    '''
    def login(self, username=None, password=None):
        self.debug('------LOGIN------')

        # if logging in with same user/passwd, check for login cookie
        if hasattr(self, 'username') and \
           hasattr(self, 'password') and \
           (username is None or self.username == username) and \
           (password is None or self.password == password) and \
           self.logged_in:
            self.debug('logged in -> cookie exists')
            self.debug('------END LOGIN------')
            return True

        # user/passwd from params overwites known user/passwd
        self.username = username or self.username if hasattr(self, 'username') else username
        self.password = password or self.password if hasattr(self, 'password') else password
        if self.username is None or self.password is None:
            # if instance doesn't have username or password, cannot login
            raise UnifiLoginError('Missing login information')

        # login with clean slate session
        self.clean_session()

        # make login call
        r = self.session.post(
            self.endpoint('/api/login'),
            headers={'Referer': self.endpoint('/login')},
            json={
                'username': self.username,
                'password': self.password,
            },
            timeout=4
        )

        # debug messages
        self.debug('LOGIN REQUEST')
        self.debug('url:', r.request.url)
        self.debug('body:', r.request.body.decode())
        self.debug('headers:', r.request.headers)
        self.debug('LOGIN RESPONSE')
        self.debug('status:', r.status_code)
        self.debug('text:', r.text)
        self.debug('headers:', r.headers)
        self.debug('cookies:', r.cookies)
        self.debug('------END LOGIN------')

        return self.logged_in

    def logout(self):
        if not self.logged_in:
            return False
        self.post(self.endpoint('/logout'))
        self.clean_session()
        return True

    def datetemp(self, a):
        '''
            Convert datetime to timestamp
        '''
        return int(datetime.timestamp(a)*1000)

    @requires_login
    @guard(models.authorize_guest_params)
    def authorize_guest(self, client_mac, minutes, site=None, ap_mac=None, up_speed=None, down_speed=None, MB_limit=None):
        '''
            Authorize a client device
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac address
                minutes     |   True    | minutes (from now) until authorization expires
                site        |   False   | site name to authorize guest, if not provided, `find_device` will be used (or `default` if ap_mac wasn't provided)
                ap_mac      |   False   | access point the client is connected (faster auth)
                up_speed    |   False   | upload speed limit in kbps
                down_speed  |   False   | download speed limit in kbps
                MB_limit    |   False   | data transfer limit in MB
        '''
        data = {
            'cmd': 'authorize-guest',
            'mac': client_mac.lower(),
            'minutes': minutes,
        }
        if up_speed is not None:
            data['up'] = up_speed
        if down_speed is not None:
            data['down'] = down_speed
        if ap_mac is not None:
            site = self.find_device(ap_mac) if site is None else site
            assert site is not None, 'No site provided and AP does not belong to any known site'
            data['ap_mac'] = ap_mac
        if MB_limit is not None:
            data['MB_limit'] = MB_limit
        self.debug('Posting authorize guest: %s' % data)
        r = self.post(self.endpoint('/api/s/%s/cmd/stamgr' % site), json=data, timeout=6)
        return self.process_response(r, boolean=True)

    @requires_login
    @guard(cmd=t.String, client_mac=models.MacAddress, site=models.SiteName)
    def _guest_cmd(self, cmd, client_mac, site):
        '''
            Run most stamgr command
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                cmd         |   True    | command to run
                client_mac  |   True    | client mac address
                site        |   True    | site name to authorize guest
        '''
        data = {
            'cmd': cmd,
            'mac': client_mac,
        }

        r = self.post(self.endpoint('/api/s/%s/cmd/stamgr' % site), json=data, timeout=6)
        return self.process_response(r, boolean=True)

    @guard(client_mac=models.MacAddress, site=models.SiteName)
    def unauthorize_guest(self, client_mac, site='default'):
        '''
            Unauthorize a client device
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac address
                site        |   False   | site name to authorize guest, defaults to `default`
        '''
        return self._guest_cmd('unauthorize-guest', client_mac, site)

    @guard(client_mac=models.MacAddress, site=models.SiteName)
    def reconnect_sta(self, client_mac, site='default'):
        '''
            Reconnect a client device
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac address
                site        |   True    | site name to authorize guest, defaults to `default`
        '''
        return self._guest_cmd('kick-sta', client_mac, site)

    @guard(client_mac=models.MacAddress, site=models.SiteName)
    def block_sta(self, client_mac, site='default'):
        '''
            Block a client device
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac address
                site        |   True    | site name to authorize guest, defaults to `default`
        '''
        return self._guest_cmd('block-sta', client_mac, site)

    @guard(client_mac=models.MacAddress, site=models.SiteName)
    def unblock_sta(self, client_mac, site='default'):
        '''
            Unblock a client device
            -------------------------
            returns True on success
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac address
                site        |   True    | site name to authorize guest, defaults to `default`
        '''
        return self._guest_cmd('unblock-sta', client_mac, site)

    @requires_login
    @guard(client_macs=t.List(models.MacAddress), site=models.SiteName)
    def forget_sta(self, client_macs, site='default'):

        data = {
            'cmd': 'forget-sta',
            'mac': client_macs,
        }

        r = self.post(self.endpoint('/api/s/%s/cmd/stamgr' % site), json=data, timeout=6)
        return self.process_response(r, boolean=True)

    @requires_login
    def list_sites(self):
        '''
            List sites managed by controller
            -------------------------
            returns an array of site info on success
        '''
        r = self.get(self.endpoint('/api/self/sites'))
        return self.process_response(r)

    @requires_login
    @guard(site=models.SiteName, device_mac=t.Or(models.MacAddress, t.Atom(None)))
    def list_devices(self, site='default', device_mac=None):
        '''
            List devices managed by controller on a given site
            -------------------------
            returns an array of devices info on success
            params:
                Name        | required  | description
                -----------------------------------------
                site        |   True    | site name to authorize guest, defaults to `default`
                device_mac  |   False   | device mac address
        '''
        # r = self.get(self.endpoint('/api/s/%s/stat/device/%s' % (site, device_mac.lower().replace(':', '').replace('-', '') or '')))
        r = self.get(self.endpoint('/api/s/%s/stat/device/%s' % (site, device_mac or '')))
        return self.process_response(r)

    @guard(device_mac=models.MacAddress)
    def find_device(self, device_mac):
        '''
            Find site name of device by mac
            -------------------------
            returns site name where device is located or None if
            device is not managed by this controller
            params:
                Name        | required  | description
                -----------------------------------------
                device_mac  |   True   | device mac address

            # This is a costly function, use with caution
        '''
        for s in self.list_sites():
            if device_mac in [models.MacAddress(d['mac']) for d in self.list_devices(site=s['name'])]:
                return models.SiteName(s['name'])

    # skipping user management functions for now

    # Sessions?

    @requires_login
    @guard(models.list_sessions_params)
    def list_sessions(self, client_mac=None, client_type='all', start=None, end=None, site='default'):
        '''
            Get all login sessions
            -------------------------
            returns an array of login sessions for all clients on a site, or a single client
            params:
                Name        | required  | description
                -----------------------------------------
                client_type |   False   | type of client, can be: ['all', 'guest', 'user']
                client_mac  |   False   | client mac to get sessions, if not provided, all sessions will be returned
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get sessions, defaults to `default`
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - 7*24*60*60*1000 if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'type': client_type,
            'start': start,
            'end': end,
        }
        if client_mac is not None:
            data['mac'] = client_mac

        r = self.get(self.endpoint('/api/s/%s/stat/session' % site), json=data)
        return self.process_response(r)

    @requires_login
    @guard(client_mac=models.MacAddress, limit=t.Int, site=models.SiteName)
    def list_sessions_latest(self, client_mac, limit=5, site='default'):
        '''
            Get latest login sessions for a given client
            -------------------------
            returns an array of login sessions for a single client on a site
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac to get sessions
                limit       |   False   | latest `limit` sessions will be returned, defaults to 5
                site        |   False   | site name to get sessions, defaults to `default`
        '''
        data = {
            'mac': client_mac,
            '_limit': limit,
            '_sort': '-assoc_time',
        }

        r = self.get(self.endpoint('/api/s/%s/stat/session' % site), json=data)
        return self.process_response(r)

    @requires_login
    @guard(models._base_time_site_params)
    def list_authorizations(self, start=None, end=None, site='default'):
        '''
            Get latest authorizations for a given site
            -------------------------
            returns an array of login sessions for a single client on a site
            params:
                Name        | required  | description
                -----------------------------------------
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get authorizations, defaults to `default`
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - 7*24*60*60*1000 if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'start': start,
            'end': end,
        }

        r = self.get(self.endpoint('/api/s/%s/stat/authorization' % site), json=data)
        return self.process_response(r)

    @requires_login
    @guard(last_hours=t.Int, site=models.SiteName)
    def list_allusers(self, last_hours=365*24, site='default'):
        '''
            Get all users ever connected to a given site
            -------------------------
            returns an array of client devices
            params:
                Name        | required  | description
                -----------------------------------------
                last_hours  |   False   | last `last_hours` to get users from, defaults to 1y (365*24 hours)
                site        |   False   | site name to get authorizations, defaults to `default`

            # the stats returned are not affected by `last_hours` parameter since they're all-time stats for the device
        '''
        data = {
            'type': 'all',
            'conn': 'all',
            'within': last_hours,
        }

        r = self.get(self.endpoint('/api/s/%s/stat/allusers' % site), json=data)
        return self.process_response(r)

    @requires_login
    @guard(last_hours=t.Int, site=models.SiteName)
    def list_guests(self, last_hours=365*24, site='default'):
        '''
            Get all guests ever connected to a given site, only valid accesses
            -------------------------
            returns an array of guest devices
            params:
                Name        | required  | description
                -----------------------------------------
                last_hours  |   False   | last `last_hours` to get guests from, defaults to 1y (365*24 hours)
                site        |   False   | site name to get authorizations, defaults to `default`
        '''
        data = {
            'within': last_hours,
        }

        r = self.get(self.endpoint('/api/s/%s/stat/guest' % site), json=data)
        return self.process_response(r)

    @requires_login
    @guard(client_mac=t.Or(models.MacAddress, t.Atom(None)), site=models.SiteName)
    def list_online_clients(self, client_mac=None, site='default'):
        '''
            Get online client devices on a given site
            -------------------------
            returns an array of guest devices
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   False   | client mac to search, if not provided all clients will be returned
                site        |   False   | site name to get authorizations, defaults to `default`
        '''
        data = {
            'within': last_hours,
        }

        r = self.get(self.endpoint('/api/s/%s/stat/sta/%s' % (site, client_mac or '')), json=data)
        return self.process_response(r)

    @requires_login
    @guard(client_mac=models.MacAddress, site=models.SiteName)
    def client_info(self, client_mac, site='default'):
        '''
            Get client device information
            -------------------------
            returns an object with client device information
            params:
                Name        | required  | description
                -----------------------------------------
                client_mac  |   True    | client mac to search
                site        |   False   | site name to get authorizations, defaults to `default`
        '''
        r = self.get(self.endpoint('/api/s/%s/stat/user/%s' % (site, client_mac)))
        return self.process_response(r)


    # Site stats

    @requires_login
    @guard(models.site_stats_params.merge(models._inner_stats_extras))
    def _site_stats(self, gran, def_range, start=None, end=None, site='default'):
        '''
            Get site stats
            -------------------------
            returns an array of stats for the given site
            params:
                Name        | required  | description
                -----------------------------------------
                gran        |   True    | granularity of the stats, only permitted: 5minutes, hourly, daily
                def_range   |   True    | default range for the stats, only used if start wasn't given
                start       |   False   | Unix timestamp in seconds or datetime, defaults to `end - def_range`
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get stats, defaults to `default`

            # support and restrictions apply from 'site_stat_*' functions
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - def_range if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'attrs': ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta', 'lan-num_sta', 'wlan-num_sta', 'time'],
            'start': start,
            'end': end,
        }
        r = self.get(self.endpoint('/api/s/%s/stat/report/%s.site' % (site, gran)), json=data)
        return self.process_response(r)


    # site stats: 5 min
    @guard(models.site_stats_params)
    def site_stat_5min(self, start=None, end=None, site='default'):
        '''
            Get site stats (5 min)
            -------------------------
            returns an array of 5 min stats for the given site
            params:
                Name        | required  | description
                -----------------------------------------
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get stats, defaults to `default`

            # supported from versions 5.5.* and later
            # retention policy for 5 minutes stats must be set accordingly
        '''
        return self._site_stats('5minutes', 12*60*60*1000, start, end, site)

    # site stats: hourly
    @guard(models.site_stats_params)
    def site_stat_hourly(self, start=None, end=None, site='default'):
        '''
            Get site stats (hourly)
            -------------------------
            returns an array of hourly stats for the given site
            params:
                Name        | required  | description
                -----------------------------------------
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get stats, defaults to `default`

            # bytes not supported from versions 4.9.1 and later
        '''
        return self._site_stats('hourly', 7*24*60*60*1000, start, end, site)

    # site stats: daily
    @guard(models.site_stats_params)
    def site_stat_daily(self, start=None, end=None, site='default'):
        '''
            Get site stats (daily)
            -------------------------
            returns an array of daily stats for the given site
            params:
                Name        | required  | description
                -----------------------------------------
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 30d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site name to get stats, defaults to `default`

            # bytes not supported from versions 4.9.1 and later
        '''
        return self._site_stats('daily', 30*24*60*60*1000, start, end, site)

    # AP stats

    @requires_login
    @guard(models.ap_stats_params.merge(models._inner_stats_extras))
    def _ap_stats(self, gran, def_range, ap_mac=None, start=None, end=None, site=None):
        '''
            Get ap stats
            -------------------------
            returns an array of stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                gran        |   True    | granularity of the stats, only permitted: 5minutes, hourly, daily
                def_range   |   True    | default range for the stats, only used if start wasn't given
                ap_mac      |   False   | mac address of the ap
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site of the ap, if not provided `find_device` will be used (or `default` if ap_mac wasn't provided)

            # support and restrictions apply from 'ap_stat_*' functions
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - def_range if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'attrs': ['bytes', 'num_sta', 'time'],
            'start': start,
            'end': end,
        }

        if ap_mac is not None:
            site = self.find_device(ap_mac) if site is None else site
            assert site is not None, 'No site provided and AP does not belong to any known site'
            data['mac'] = ap_mac
        elif site is None:
            site = 'default'

        r = self.get(self.endpoint('/api/s/%s/stat/report/%s.ap' % (site, gran)), json=data)
        return self.process_response(r)

    # ap stats: 5 min
    @guard(models.ap_stats_params)
    def ap_stat_5min(self, ap_mac=None, start=None, end=None, site=None):
        '''
            Get ap stats (5 min)
            -------------------------
            returns an array of 5 min stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                ap_mac      |   False   | mac address of the ap
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site of the ap, if not provided `find_device` will be used (or `default` if ap_mac wasn't provided)

            # supported from versions 5.5.* and later
            # retention policy for 5 minutes stats must be set accordingly
        '''
        return self._ap_stats('5minutes', 12*60*60*1000, ap_mac, start, end, site)

    # ap stats: hourly
    @guard(models.ap_stats_params)
    def ap_stat_hourly(self, ap_mac=None, start=None, end=None, site=None):
        '''
            Get ap stats (hourly)
            -------------------------
            returns an array of hourly stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                ap_mac      |   False   | mac address of the ap
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site of the ap, if not provided `find_device` will be used (or `default` if ap_mac wasn't provided)

            # versions < 4.6.6 keep up to 5 hours of these stats
        '''
        return self._ap_stats('hourly', 7*24*60*60*1000, ap_mac, start, end, site)

    # ap stats: daily
    @guard(models.ap_stats_params)
    def ap_stat_daily(self, ap_mac=None, start=None, end=None, site=None):
        '''
            Get ap stats (daily)
            -------------------------
            returns an array of daily stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                ap_mac      |   True    | mac address of the ap
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site of the ap, if not provided `find_device` will be used (or `default` if ap_mac wasn't provided)

            # versions < 4.6.6 keep up to 5 hours of these stats
        '''
        return self._ap_stats('daily', 7*24*60*60*1000, ap_mac, start, end, site)

    @requires_login
    @guard(models.user_stats_params.merge(models._inner_stats_extras))
    def _user_stats(self, gran, def_range, user_mac, attrs=['rx_bytes', 'tx_bytes'], start=None, end=None, site=None):
        '''
            Get ap stats
            -------------------------
            returns an array of stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                gran        |   True    | granularity of the stats, only permitted: 5minutes, hourly, daily
                def_range   |   True    | default range for the stats, only used if start wasn't given
                user_mac    |   True    | mac address of the user
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site?
                attrs       |   False   | list of attributes to be returned, defalts to [rx_bytes, tx_bytes]

            # support and restrictions apply from 'user_stat_*' functions
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - def_range if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'mac': user_mac,
            'attrs': attrs if 'time' in attrs else attrs.append('time'),
            'start': start,
            'end': end,
        }

        # site?

        r = self.get(self.endpoint('/api/s/%s/stat/report/%s.user' % (site, gran)), json=data)
        return self.process_response(r)

    @guard(models.user_stats_params)
    def user_stat_5min(self, user_mac, attrs=['rx_bytes', 'tx_bytes'], start=None, end=None, site=None):
        '''
            Get user/client stats (5 min)
            -------------------------
            returns an array of 5 min stats for the given user/client
            params:
                Name        | required  | description
                -----------------------------------------
                user_mac    |   True    | mac address of the user
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site?
                attrs       |   False   | list of attributes to be returned, defalts to [rx_bytes, tx_bytes]

            # Possible values for attrs:
                - rx_bytes
                - tx_bytes
                - signal
                - rx_rate
                - tx_rate
                - rx_retries
                - tx_retries
                - rx_packets
                - tx_packets

            # supported from versions 5.8.* and later
            # retention policy for 5 minutes stats must be set accordingly
            # "Clients Historical Data" must be enabled (controller settings on Maintenance section)
        '''
        return self._user_stats('5minutes', 12*60*60*1000, user_mac, attrs, start, end, site)

    @guard(models.user_stats_params)
    def user_stat_hourly(self, user_mac, attrs=['rx_bytes', 'tx_bytes'], start=None, end=None, site=None):
        '''
            Get user/client stats (hourly)
            -------------------------
            returns an array of hourly stats for the given user/client
            params:
                Name        | required  | description
                -----------------------------------------
                user_mac    |   True    | mac address of the user
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site?
                attrs       |   False   | list of attributes to be returned, defalts to [rx_bytes, tx_bytes]

            # Possible values for attrs:
                - rx_bytes
                - tx_bytes
                - signal
                - rx_rate
                - tx_rate
                - rx_retries
                - tx_retries
                - rx_packets
                - tx_packets

            # supported from versions 5.8.* and later
            # "Clients Historical Data" must be enabled (controller settings on Maintenance section)
        '''
        return self._user_stats('hourly', 7*24*60*60*1000, user_mac, attrs, start, end, site)

    @guard(models.user_stats_params)
    def user_stat_daily(self, user_mac, attrs=['rx_bytes', 'tx_bytes'], start=None, end=None, site=None):
        '''
            Get user/client stats (daily)
            -------------------------
            returns an array of daily stats for the given user/client
            params:
                Name        | required  | description
                -----------------------------------------
                user_mac    |   True    | mac address of the user
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site?
                attrs       |   False   | list of attributes to be returned, defalts to [rx_bytes, tx_bytes]

            # Possible values for attrs:
                - rx_bytes
                - tx_bytes
                - signal
                - rx_rate
                - tx_rate
                - rx_retries
                - tx_retries
                - rx_packets
                - tx_packets

            # supported from versions 5.8.* and later
            # "Clients Historical Data" must be enabled (controller settings on Maintenance section)
        '''
        return self._user_stats('daily', 7*24*60*60*1000, user_mac, attrs, start, end, site)

    # gateway

    @requires_login
    @guard(models.gateway_stats_params.merge(models._inner_stats_extras))
    def _gateway_stats(self, gran, def_range, attrs=['mem', 'cpu', 'loadavg_5'], start=None, end=None, site='default'):
        '''
            Get gateway stats
            -------------------------
            returns an array of stats for the given ap or for all aps on a given site
            params:
                Name        | required  | description
                -----------------------------------------
                gran        |   True    | granularity of the stats, only permitted: 5minutes, hourly, daily
                def_range   |   True    | default range for the stats, only used if start wasn't given
                attrs       |   False   | list of attributes to be returned, defalts to [mem, cpu, loadavg_5]
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site where the USG is located

            # support and restrictions apply from 'gateway_stat_*' functions
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - def_range if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'attrs': attrs if 'time' in attrs else attrs.append('time'),
            'start': start,
            'end': end,
        }

        r = self.get(self.endpoint('/api/s/%s/stat/report/%s.gw' % (site, gran)), json=data)
        return self.process_response(r)

    @guard(models.gateway_stats_params)
    def gateway_stat_5min(self, attrs=['mem', 'cpu', 'loadavg_5'], start=None, end=None, site='default'):
        '''
            Get gateway stats (5 min)
            -------------------------
            returns an array of 5 min stats for the given gateway belonging to the given site
            params:
                Name        | required  | description
                -----------------------------------------
                attrs       |   False   | list of attributes to be returned, defalts to [mem, cpu, loadavg_5]
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 12h
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site where the USG is located

            # Possible values for attrs:
                - mem
                - cpu
                - loadavg_5
                - lan-rx_errors
                - lan-tx_errors
                - lan-rx_bytes
                - lan-tx_bytes
                - lan-rx_packets
                - lan-tx_packets
                - lan-rx_dropped
                - lan-tx_dropped

            # supported from versions 5.5.* and later
            # retention policy for 5 minutes stats must be set accordingly
            # must have a USG on the site
        '''
        return self._gateway_stats('5minutes', 12*60*60*1000, attrs, start, end, site)

    @guard(models.gateway_stats_params)
    def gateway_stat_hourly(self, attrs=['mem', 'cpu', 'loadavg_5'], start=None, end=None, site='default'):
        '''
            Get gateway stats (hourly)
            -------------------------
            returns an array of hourly stats for the given gateway belonging to the given site
            params:
                Name        | required  | description
                -----------------------------------------
                attrs       |   False   | list of attributes to be returned, defalts to [mem, cpu, loadavg_5]
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 7d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site where the USG is located

            # Possible values for attrs:
                - mem
                - cpu
                - loadavg_5
                - lan-rx_errors
                - lan-tx_errors
                - lan-rx_bytes
                - lan-tx_bytes
                - lan-rx_packets
                - lan-tx_packets
                - lan-rx_dropped
                - lan-tx_dropped

            # must have a USG on the site
        '''
        return self._gateway_stats('hourly', 7*24*60*60*1000, attrs, start, end, site)

    @guard(models.gateway_stats_params)
    def gateway_stat_daily(self, attrs=['mem', 'cpu', 'loadavg_5'], start=None, end=None, site='default'):
        '''
            Get user/client stats (daily)
            -------------------------
            returns an array of daily stats for the given gateway belonging to the given site
            params:
                Name        | required  | description
                -----------------------------------------
                attrs       |   False   | list of attributes to be returned, defalts to [mem, cpu, loadavg_5]
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 1y
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site where the USG is located

            # Possible values for attrs:
                - mem
                - cpu
                - loadavg_5
                - lan-rx_errors
                - lan-tx_errors
                - lan-rx_bytes
                - lan-tx_bytes
                - lan-rx_packets
                - lan-tx_packets
                - lan-rx_dropped
                - lan-tx_dropped

            # must have a USG on the site
        '''
        return self._gateway_stats('daily', 365*24*60*60*1000, attrs, start, end, site)

    @requires_login
    @guard(models._base_time_site_params)
    def speedtest_result(self, start=None, end=None, site='default'):
        '''
            Get speed test results
            -------------------------
            returns an array of speedtest results for the USG on the given site
            params:
                Name        | required  | description
                -----------------------------------------
                start       |   False   | Unix timestamp in seconds or datetime, defaults to end - 1d
                end         |   False   | Unix timestamp in seconds or datetime, defaults to now
                site        |   False   | site where the USG is located

            # must have a USG on the site
        '''
        end = end*1000 if isinstance(end, int) else int(datetime.now().timestamp()*1000) if end is None else int(end.timestamp()*1000)
        start = start*1000 if isinstance(start, int) else end - 24*60*60*1000 if start is None else int(start.timestamp()*1000)
        assert 0 < start < end, 'start must be before end (and both positive)'

        data = {
            'attrs': ['xput_download', 'xput_upload', 'latency', 'time'],
            'start': start,
            'end': end,
        }
        r = self.get(self.endpoint('/api/s/%s/stat/report/archive.speedtest' % site), json=data)
        return self.process_response(r)

    @requires_login
    def stat_deviceBasic(self, site):
        '''
            Get all AP mac's from this site.
            site = 'site code'

            Response:
                type: uap is AP, usw is Switch
        '''
        r = self.get(self.endpoint('/api/s/{}/stat/device-basic' .format(site)))
        return self.process_response(r)

    @requires_login
    def stat_device(self, site, macs=None):
        '''
            List all params from dashboad/clients, include all activeclients, client ap conected, active down/up per client, ip, name, wlan, channel and others stats.
            Case macs is None, this request bring data from all AP's. Case especific mac in this request, this request bring data from this AP's.
            -
            Required: site[site code string]
            Optional: macs[array of macs]
            Example:
                {"macs":["f0:9f:c2:33:94:27", "f0:9f:c2:33:94:27"]}
        '''
        json = {"macs": macs}
        r = self.post(self.endpoint('/api/s/{}/stat/device' .format(site)), json=json, timeout=4)
        return self.process_response(r)

    @requires_login
    def stat_reportSite(self, site, date_range, interval='daily', attrs=None):
        '''
            This request get total user and traffic per interval
            Required: site, date_range(tuple in datetime)
            Optional:
                      macs: Array of AP mac's
                      date_range: tuple of datetime range
                      interval: daily, hourly, 5minutes. Default is 'daily'
                      attrs: aditional filters, default is ["bytes","num_sta","time"]
        '''
        assert date_range, "date_range is required"
        data = {"start": self.datetemp(date_range[0]), "end": self.datetemp(date_range[1])}
        if (attrs == None):
            data["attrs"] = [
                "wlan_bytes",
                "wlan-num_sta",
                "time"]
        else:
            data["attrs"] = attrs
        r = self.post(self.endpoint('/api/s/{}/stat/report/{}.site' .format(site, interval)), json=data)
        return self.process_response(r)

    @requires_login
    def stat_reportAp(self, site, date_range, macs=None, interval='daily', attrs=None):
        '''
            Required: site, date_range(tuple in datetime)
            Optional:
                      date_range: tuple of datetime range
                      macs: Array of AP mac's
                      interval: daily, hourly, 5minutes. Default is 'daily'
                      attrs: Aditional filters, default is ["bytes","num_sta","time"]
        '''
        data = {
            "start": self.datetemp(date_range[0]),
            "end": self.datetemp(date_range[1])}
        if (attrs == None):
            data["attrs"] = ["bytes", "num_sta","time"]
        else:
            data["attrs"] = attrs
        r = self.post(self.endpoint('/api/s/{}/stat/report/{}.ap' .format(site, interval)), json=data, timeout=4)
        return self.process_response(r)

    @requires_login
    def stat_widgetHealth(self, site):
        '''
            List AP's and Switchs adopted, connected, disconnected, pending and disable
            UAP = AP
            USW = SWITCH
            UGW = UNIFI GATEWAY?
        '''
        r = self.post(self.endpoint('/api/s/{}/stat/widget/health' .format(site)))
        return self.process_response(r)

    @requires_login
    def stat_clients(self, site):
        '''
            List all users connected, pending and others stats.
        '''
        r = self.get(self.endpoint('/api/s/{}/stat/sta' .format(site)))
        return self.process_response(r)
