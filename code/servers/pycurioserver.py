# pycurioserver.py

from curio import run, spawn
from curio.socket import *  # pylint: disable=unused-wildcard-import, wildcard-import


async def echo_client(conn, addr):
    print(f'Got a connection from {addr}')
    async with conn:
        while True:
            data = await conn.recv(8192)
            if not data:
                break
            await conn.sendall(data)


async def echo_server(addr):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sock.bind(addr)
    sock.listen(1)
    async with sock:
        while True:
            conn, addr = await sock.accept()
            await spawn(echo_client, conn, addr, daemon=True)


if __name__ == '__main__':
    run(echo_server, ('', 25000))
