# pubsub.py

from curio import run, TaskGroup, sleep, Queue

messages = Queue()
subscribers = set()

async def dispatcher():
    async for msg in messages:
        for q in subscribers:
            await q.put(msg)


async def subscriber(name):
    queue = Queue()
    subscribers.add(queue)
    print(f'{name} added itself to the list of subscribers')
    try:
        async for msg in queue:
            print(f'{name} got {msg}')
    finally:
        subscribers.discard(queue)


async def publish(msg):
    await messages.put(msg)


async def producer():
    for i in range(10):
        print(f'pushing {i}')
        await publish(i)
        await sleep(1)

async def main():
    async with TaskGroup() as g:
        await g.spawn(dispatcher)
        await g.spawn(subscriber, 'sub1')
        await g.spawn(subscriber, 'sub2')

        ptask = await g.spawn(producer)
        await ptask.join()
        await g.cancel_remaining()

if __name__ == '__main__':
    run(main, with_monitor=True)
