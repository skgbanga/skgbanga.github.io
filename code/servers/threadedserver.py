import threading
from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import


def echo_handler(address, request):
    print('Got a connection from ', address)
    while True:
        msg = request.recv(8192)
        if not msg:
            break
        request.sendall(msg)
    request.close()


def threaded_server(address, backlog=5):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(address)
    sock.listen(backlog)
    while True:
        request, addr = sock.accept()
        t = threading.Thread(
            target=echo_handler, args=(addr, request), daemon=True)
        t.start()


if __name__ == '__main__':
    threaded_server(('', 25000))
