# pyasyncioserver.py

import asyncio


async def handle_echo(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'Got a connection from {addr}')
    while True:
        data = await reader.read(8192)
        if not data:
            break
        writer.write(data)
        await writer.drain()

    writer.close()


loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_echo, '', 25000, loop=loop)
server = loop.run_until_complete(coro)  # this doesn't block


loop.run_forever()
