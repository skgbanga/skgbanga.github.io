# pyyieldserver.py

from socket import *  # pylint: disable=unused-wildcard-import, wildcard-import
from collections import deque
import select

tasks = deque()
want_read = {}
want_write = {}

def run():
    while any([tasks, want_read, want_write]):
        while not tasks:
            # wait for io
            can_read, can_write, _ = select.select(want_read, want_write, [])
            for r in can_read:
                tasks.append(want_read.pop(r))
            for w in can_write:
                tasks.append(want_write.pop(w))

        task = tasks.popleft()
        action, actor = next(task)
        if action == 'recv':
            want_read[actor] = task
        elif action == 'send':
            want_write[actor] = task


def echo_client(client, addr):
    print('Got a connection from ', addr)
    while True:
        yield 'recv', client
        msg = client.recv(8192) # blocking
        if msg is None:
            break
        yield 'send', client
        client.sendall(msg) # blocking
    client.close()
    tasks.remove(client)

def echo_server(address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(address)
    sock.listen(1)
    while True:
        yield 'recv', sock
        client, addr = sock.accept() # blocking
        tasks.append(echo_client(client, addr))

if __name__ == '__main__':
    server = echo_server(('', 25000))
    tasks.append(server)
    run()
