# pyselectorserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import


def echo_client(addr, client):
    print(f'Got a connection from {addr}')
    while True:
        msg = client.recv(8192)
        if not msg:
            break
        client.sendall(msg)
    client.close()

def echo_server(addr):
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(addr)
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        echo_client(addr, client)


if __name__ == '__main__':
    echo_server(('', 25000))
