#!/usr/bin/python3

import types
import heapq
import time


#####
# Library code

@types.coroutine
def sleep(seconds):
    yield seconds

class Task:
    def __init__(self, wakeup_time, coro):
        self.wakeup_time = wakeup_time
        self.coro = coro

    def __lt__(self, other):
        return self.wakeup_time < other.wakeup_time

class Loop:
    def __init__(self, *coros):
        self.coros = coros
        self.tasks = []

    def run_until_completion(self):
        # run all the coros
        for coro in self.coros:
            now = time.time()
            secs = coro.send(None)
            self.tasks.append(Task(now + secs, coro))

        while self.tasks:
            task = heapq.heappop(self.tasks)
            now = time.time()
            if now < task.wakeup_time:
                # sleep for sometime as nothing to do
                time.sleep(task.wakeup_time - now)

            # time to do work
            try:
                secs = task.coro.send(None)
            except StopIteration:
                pass
            else:
                heapq.heappush(self.tasks, Task(task.wakeup_time + secs,
                    task.coro))

#####
# User code

# coroutine based way of doing things
async def countdown(identifier, delay):
    for i in range(10):
        await sleep(delay)
        print(f'{identifier}: {i}')

if __name__ == '__main__':
    loop = Loop(countdown('A', 1), countdown('B', 2))
    loop.run_until_completion()
