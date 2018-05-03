# pyselectorserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import

def echo_client(addr, conn):
    print(f'Got a connection from {addr}')
    with conn:
        while True:
            msg = conn.recv(8192)
            if not msg:
                break
            conn.sendall(msg)

def echo_server(addr):
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(addr)
    sock.listen(1)
    with sock:
        while True:
            conn, addr = sock.accept()
            echo_client(addr, conn)


if __name__ == '__main__':
    echo_server(('', 25000))
