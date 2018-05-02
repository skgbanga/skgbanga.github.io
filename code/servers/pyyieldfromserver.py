# pyyieldfromserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import
import selectors

selector = selectors.DefaultSelector()


class Future:

    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, callback):
        self._callbacks.append(callback)

    def set_result(self, value):
        self.result = value
        for cb in self._callbacks:
            cb(self)


class Task:

    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)
        self.step(f)

    def step(self, future):
        try:
            next_future = self.coro.send(future.result)
        except StopIteration:
            return

        next_future.add_done_callback(self.step)


def connect(sock):
    f = Future()

    def on_connected(conn, mask):  # pylint: disable=unused-argument
        f.set_result(None)

    selector.register(sock, selectors.EVENT_READ, on_connected)
    yield f
    selector.unregister(sock)
    conn, addr = sock.accept()
    return conn, addr


def recv(sock):
    f = Future()

    def on_recv(conn, mask):  # pylint: disable=unused-argument
        f.set_result(None)

    selector.register(sock, selectors.EVENT_READ, on_recv)
    yield f
    selector.unregister(sock)

    data = sock.recv(8192)
    return data

def send(sock, msg):
    f = Future()

    def on_send(conn, mask): # pylint: disable=unused-argument
        f.set_result(None)

    selector.register(sock, selectors.EVENT_WRITE, on_send)
    yield f
    selector.unregister(sock)
    sock.sendall(msg)


def loop():
    while True:
        events = selector.select()
        for key, mask in events:
            func = key.data
            func(key.fileobj, mask)


def echo_client(addr, conn):
    print(f"Got a connection from {addr}")
    while True:
        msg = yield from recv(conn)
        if not msg:
            break
        yield from send(conn, msg)
    conn.close()


def echo_server(addr):
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(addr)
    sock.listen(1)
    sock.setblocking(False)

    while True:
        conn, addr = yield from connect(sock)
        Task(echo_client(addr, conn))


if __name__ == "__main__":
    Task(echo_server(("", 25000)))
    loop()
