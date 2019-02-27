import socket
from selectors import DefaultSelector, EVENT_WRITE

selector = DefaultSelector()

sock = socket.socket()
sock.setblocking(False)
try:
    sock.connect(('www.baidu.com', 80))
except BlockingIOError:
    pass


def connected():
    selector.unregister(sock.fileno())
    print('connected!')


selector.register(sock.fileno(), EVENT_WRITE, connected)
