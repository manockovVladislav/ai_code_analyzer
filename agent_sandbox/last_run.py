import os
import socket
os.environ['NO_NETWORK'] = '1'
def _blocked(*args, **kwargs):
    raise RuntimeError('Network is disabled in agent_sandbox')
socket.socket = _blocked
socket.create_connection = _blocked
try:
    import urllib.request
    urllib.request.urlopen = _blocked
except Exception:
    pass
try:
    import requests
    requests.sessions.Session.request = _blocked
except Exception:
    pass

print("2 + 2 =", 2 + 2)
import socket

try:
    socket.socket()
except Exception as e:
    print("Сеть заблокирована:", type(e).__name__, str(e))