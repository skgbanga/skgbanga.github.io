# threadpool.py

# bad implementation of threadpool

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import
from threading import Thread
from queue import Queue


def echo_client(q):
    sock, addr = q.get()
    print('Got a connection from addr', addr)
    while True:
        msg = sock.recv(8192)
        if not msg:
            break
        sock.sendall(msg)
    print('Connection closed')
    sock.close()

def echo_server(addr, nworkers=5):
    q = Queue()
    for _ in range(nworkers):
        t = Thread(target=echo_client, args=(q,), daemon=True)
        t.start()

    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(addr)
    sock.listen(5)

    while True:
        client_socket, client_addr = sock.accept()
        q.put((client_socket, client_addr))

if __name__ == '__main__':
    echo_server(('', 21000))
