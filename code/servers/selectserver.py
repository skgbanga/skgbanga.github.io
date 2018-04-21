# selectserver.py

import select
from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import


def event_loop(handlers):
    while True:
        wants_recv = [h for h in handlers if h.wants_to_recv()]
        wants_send = [h for h in handlers if h.wants_to_send()]
        can_recv, can_send, _ = select.select(wants_recv, wants_send, [])
        for h in can_recv:
            h.handle_recv()
        for h in can_send:
            h.handle_send()


class EventHandler:
    # event handler has to implement fileno function
    # for select call to work correctly
    def fileno(self):
        raise NotImplementedError('must implement fileno function')

    def wants_to_recv(self):  # pylint: disable=no-self-use
        return False

    def wants_to_send(self):  # pylint: disable=no-self-use
        return False

    def handle_recv(self):
        pass

    def handle_send(self):
        pass


class TCPServer(EventHandler):
    def __init__(self, address, client_handler, handler_list):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        self.sock.bind(address)
        self.sock.listen(1)  # backlog
        self.client_handler = client_handler
        self.handler_list = handler_list

    def fileno(self):
        return self.sock.fileno()

    def wants_to_recv(self):
        return True

    def handle_recv(self):
        client, addr = self.sock.accept()
        print('Got a connection from', addr)
        self.handler_list.append(
            self.client_handler(client, self.handler_list))


# Clients have responsibility to remove themselves from the list
# of handlers
class TCPClient(EventHandler):
    def __init__(self, sock, handler_list):
        self.sock = sock
        self.handler_list = handler_list
        self.outgoing = bytearray()

    def fileno(self):
        return self.sock.fileno()

    def close(self):
        self.sock.close()
        self.handler_list.remove(self)

    def wants_to_send(self):
        return True if self.outgoing else False

    def handle_send(self):
        # don't use sendall since it can block for a while
        nsent = self.sock.send(self.outgoing)
        self.outgoing = self.outgoing[nsent:]


class TCPEchoClient(TCPClient):
    def wants_to_recv(self):
        return True

    def handle_recv(self):
        data = self.sock.recv(8192)
        if not data:
            self.close()
        else:
            self.outgoing.extend(data)


if __name__ == '__main__':
    handlers = []
    handlers.append(TCPServer(('', 17000), TCPEchoClient, handlers))
    event_loop(handlers)
