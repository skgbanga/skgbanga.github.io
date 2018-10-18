# chat.py

import logging
import signal
from curio import (run, tcp_server, TaskGroup, Queue, SignalQueue, spawn,
                   CancelledError)
from curio.debug import traptrace

messages = Queue()
participants = set()

async def dispatcher():
    async for msg in messages:
        for q in participants:
            await q.put(msg)


async def sender(conn, q):
    while True:
        async for name, msg in q:
            await conn.write(name + b': ' + msg)


async def client_handler(conn, addr):
    print('Got a connection from ', addr)
    try:
        q = Queue()
        participants.add(q)

        stream = conn.as_stream()
        outgoing = await spawn(sender, stream, q)

        await stream.write(b'Your name?\n')
        name = (await stream.readline()).strip()

        await messages.put((name, b'joined\n'))

        async for msg in stream:
            await messages.put((name, msg))
    except CancelledError:
        await stream.write(b'Server is going away!\n')
        raise
    finally:
        print('Removing', addr)
        participants.discard(q)
        await messages.put((name, b'has gone away\n'))
        await outgoing.cancel()


async def chat_server(ip, port):
    async with TaskGroup(wait=any) as f:
        await f.spawn(tcp_server, ip, port, client_handler)
        await f.spawn(dispatcher)


async def main(ip, port):
    async with SignalQueue(signal.SIGHUP) as restart:
        while True:
            print(f'Starting a server at {ip}:{port}')
            task = await spawn(chat_server, ip, port)
            await restart.get()
            print('Shutting down the server')
            await task.cancel()

def setuplogging():
    logger = logging.getLogger('curio')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('curio.log')
    logger.addHandler(fh)

if __name__ == '__main__':
    setuplogging()
    run(main, '', 25000, debug=traptrace)
