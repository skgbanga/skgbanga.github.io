#pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import

from curio import *

async def friend():
    try:
        await sleep(100)
    finally:
        print('Going away')


async def kid():
    try:
        async with TaskGroup() as f:
            await f.spawn(friend)
            await f.spawn(friend)
    finally:
        print('fine. closing')


async def parent():
    print('parent starting...')
    kid_task = await spawn(kid)
    await sleep(10)
    print('Canceling kid')
    await kid_task.cancel()
    print('parent going away')


if __name__ == '__main__':
    run(parent)
