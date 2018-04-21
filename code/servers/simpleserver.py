# simpleserver.py

from socketserver import TCPServer, BaseRequestHandler

class EchoHandler(BaseRequestHandler):
    def handle(self):
        print('Got a connection from ', self.client_address)
        while True:
            msg = self.request.recv(8192)  # blocking call
            if not msg:  # happens when the connection is closed by the user
                break
            self.request.send(msg)


if __name__ == '__main__':
    TCPServer.allow_reuse_address = True
    server = TCPServer(('', 25000), EchoHandler)
    server.serve_forever()
