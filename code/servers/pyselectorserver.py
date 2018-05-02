# basicserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import
import selectors

selector = selectors.DefaultSelector()

def accept(sock, _):
    conn, addr = sock.accept()
    print(f"Got a connection from {addr}")
    conn.setblocking(False)
    c = Connection()
    selector.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, c.handle)


class Connection:
    def __init__(self):
        self.outgoing = bytearray()

    def handle(self, conn, mask):
        if mask & selectors.EVENT_WRITE:
            if not self.outgoing:
                return

            nsent = conn.send(self.outgoing)
            self.outgoing = self.outgoing[nsent:]

        else:
            msg = conn.recv(8192)
            if msg:
                self.outgoing.extend(msg)
            else:
                selector.unregister(conn)
                conn.close()


def echo_server(address):
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(address)
    sock.listen(1)
    selector.register(sock, selectors.EVENT_READ, accept)

    while True:
        events = selector.select()
        for key, mask in events:
            func = key.data
            func(key.fileobj, mask)


if __name__ == "__main__":
    echo_server(("", 25000))
