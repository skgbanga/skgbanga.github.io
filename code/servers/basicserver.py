# basicserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import

def echo_handler(address, request):
    print('Got a connection from ', address)
    while True:
        msg = request.recv(8192)
        if not msg:
            break
        request.sendall(msg)
    request.close()


def echo_server(address, backlog=5):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(address)
    sock.listen(backlog)
    while True:
        request, addr = sock.accept()
        echo_handler(addr, request)


if __name__ == '__main__':
    echo_server(('', 25000))
