# echo.py

from curio import *

async def client_handler(conn, addr):
    print('Got a connection from ', addr)
    while True:
        msg = await conn.recv(8192)
        if not msg:
            break
        await conn.send(msg)
    print('Connection closed')


if __name__ == '__main__':
    run(tcp_server, '', 25000, client_handler)
