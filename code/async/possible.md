```
def countdown(n):
  while n > 0:
    yield n
    n -= 1
c = countdown(5)
type(c)
 = generator
```
One can call next on these generators

```
def countdown(n):
  while n > 0:
    yield n
    n -= 1
  return 'finish'
c = countdown(5)
type(c)
 = generator
```
StopIteration will have `.value` set to 'finish'


```
async def countdown(n):
  while n > 0:
    yield n
    n -= 1
  return 'finish'

> Syntax error
```


```
async def countdown(n):
  while n > 0:
    yield n
    n -= 1
c = countdown(5)
type(c)
 = async_generator

next(c)
 = TypeError: 'async_generator' object is not an iterator
```
