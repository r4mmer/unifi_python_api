# Unifi Python API

A python implementation of the Unifi controller API

### Instalation

```bash
$ pip install unifi-python-api
```

### Progress
For now, only the guest manager calls have been implemented (because that's my current use for this API).
I'm working on the tests then i'll move on to the statistics calls.

### Example usage
```python
from unifi_api import UnifiClient

unifi_controller_url = 'https://example.com:8443'

# Create the client then login
client = UnifiClient(unifi_controller_url)
client.login(username="example", password="example")

# Or both at once
client = UnifiClient(unifi_controller_url, username="example", password="example")

# Then use freely, if the session expires another login will be made automatically
# Example: authorize client for an hour
client.authorize_guest("AA-BB-CC-DD-EE-FF", 60)
```

TODO:
  - make tests with pytest
  - statistics calls

### Credits
Translated from the Unifi API client in php:
- [Art-of-WiFi]( https://github.com/Art-of-WiFi/UniFi-API-client )
Other sources:
- Bash API published by [Ubiquiti]( https://dl.ubnt.com/unifi/5.8.24/unifi_sh_api )
- Go implementation by [ipstatic]( https://github.com/ipstatic/unifi-captive-portal )
