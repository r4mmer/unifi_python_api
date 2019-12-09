from datetime import datetime
import re

import trafaret as t

class ReAndTrans(t.Regexp):
    def __init__(self, regexp, re_flags=0, trans=lambda x: x):
        super(ReAndTrans, self).__init__(regexp, re_flags)
        self.trans = trans
    def check_and_return(self, value):
        return self.trans(super(ReAndTrans, self).check_and_return(value))

def format_macaddr(mac_address):
    m = mac_address.upper().replace('-', '').replace(':', '')
    return ':'.join(m[x:x+2] for x in range(0, len(m), 2))


MacAddress = t.OnError(
    ReAndTrans(re.compile(
        r'^([0-9A-F]{2}[:-]?){5}([0-9A-F]{2})$',
        re.IGNORECASE,
    ), trans=format_macaddr),
    'value is not a MAC address',
)

SiteName = t.OnError(
    # XXX: New unifi update changes site id structure, fix for future releases
    # t.Or(t.String(min_length=8, max_length=8), t.Atom('default')),
    t.String(),
    'value is not an Unifi site id'
)

# No concrete JsonResponse structure for now, only basics
# maybe use special t.Key to map some usefull things like meta.rc (ok, error) => (True, False) in another key
JsonResponse = t.Dict({
    'data': t.Or(t.List(t.Any), t.String), # check if data is optinal, and possible values
    'meta': t.Dict({
        'rc': t.Enum('ok', 'error'), # check if other rc's could exist
        t.Key('msg', optional=True): t.String,
    }, ignore_extra='*'),
}, ignore_extra='*')

_base_time_params = t.Dict({
    'start': t.Or(t.Float, t.Type(datetime), t.Atom(None)),
    'end': t.Or(t.Float, t.Type(datetime), t.Atom(None)),
})

_base_time_site_params = _base_time_params.merge({
    'site': SiteName
})
_base_time_op_site_params = _base_time_params.merge({
    'site': t.Or(SiteName, t.Atom(None))
})

_inner_stats_extras = t.Dict({
    'gran': t.Enum('5minutes', 'hourly', 'daily'),
    'def_range': t.Int,
})

# will not check for port in base_url for now
init_params = t.Dict({
    'base_url': t.URL,
    'ssl_verify': t.Bool,
    'debug': t.Bool,
    t.Key('username', optional=True): t.Or(t.String, t.Atom(None)),
    t.Key('password', optional=True): t.Or(t.String, t.Atom(None)),
})

authorize_guest_params = t.Dict({
    'client_mac': MacAddress,
    'minutes': t.Int,
    'site': t.Or(SiteName, t.Atom(None)),
    t.Key('ap_mac', optional=True): t.Or(MacAddress, t.Atom(None)),
    t.Key('up_speed', optional=True): t.Or(t.Int, t.Atom(None)),
    t.Key('down_speed', optional=True): t.Or(t.Int, t.Atom(None)),
    t.Key('MB_limit', optional=True): t.Or(t.Int, t.Atom(None)),
})

site_stats_params = _base_time_site_params

ap_stats_params = _base_time_op_site_params.merge({'ap_mac': MacAddress})

user_stats_params = _base_time_op_site_params.merge({ # maybe not optional site
    'user_mac': MacAddress,
    'attrs': t.List(t.Enum(
        'rx_bytes',
        'tx_bytes',
        'signal',
        'rx_rate',
        'tx_rate',
        'rx_retries',
        'tx_retries',
        'rx_packets',
        'tx_packets'
    )),
})

list_sessions_params = _base_time_site_params.merge({
    'client_mac': t.Or(MacAddress, t.Atom(None)),
    'client_type': t.Enum('all', 'guest', 'user'),
})

gateway_stats_params = _base_time_site_params.merge({
    'attrs': t.List(t.Enum(
        'mem',
        'cpu',
        'loadavg_5',
        'lan-rx_errors',
        'lan-tx_errors',
        'lan-rx_bytes',
        'lan-tx_bytes',
        'lan-rx_packets',
        'lan-tx_packets',
        'lan-rx_dropped',
        'lan-tx_dropped'
    )),
})
