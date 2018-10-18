# hello.py

import curio
import requests

def fib(n):
    if n < 2:
        return 1

    return fib(n - 1) + fib(n - 2)


def fibsum():
    total = 0
    for n in range(36):
        total += fib(n)

    return total


async def friend(name):
    print('Hi, my name is', name, '. Playing minecraft...')
    try:
        await curio.sleep(100)
    except curio.CancelledError:
        print(name, 'going home')
        raise


async def countdown(n):
    while n > 0:
        print('T-minus', n)
        await curio.sleep(1)
        n -= 1


async def kid():
    print('Building the Millenium Falcon in Minecraft')

    async with curio.TaskGroup() as f:
        await f.spawn(friend, 'Max')
        await f.spawn(friend, 'Lillian')
        await f.spawn(friend, 'Thomas')

        try:
            r = await curio.run_in_thread(requests.get,
                                          f'http://www.dabeaz.com/cgi-bin/fib.py?n=50')
            resp = r.json()
            total = int(resp['value'])
            print('Sum of first 36 fib numbers is', total)

        except curio.CancelledError:
            print('Fine. Saving my work.')
            raise


async def parent():
    kid_task = await curio.spawn(kid)
    await curio.sleep(5)

    print("Let's go")

    count_task = await curio.spawn(countdown, 10)
    await count_task.join()

    print("We're leaving!")
    try:
        await curio.timeout_after(20, kid_task.join)
    except curio.TaskTimeout:
        print('I warned you!')
        await kid_task.cancel()
    print('Leaving!')


if __name__ == '__main__':
    curio.run(parent, with_monitor=True)
