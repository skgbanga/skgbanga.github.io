---
layout: post
title:  "Which core to bind your thread to?"
date:   2016-11-13 22:13:22 -0500
categories: concurrency
---
I am currently reading Anthony Williams' [C++ Concurrency in Action][book] these days. While trying to analyze the
comparative performance of various read write (shared) mutexes, a friend recommended to bind the threads to specific
cores on the machine. It turns out to be a very loaded statement. If you do `lscpu -e` on your linux box, you are going to see
output similar to this:

```
CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE MAXMHZ    MINMHZ
0   0    0      0    0:0:0:0       yes
1   0    0      1    1:1:1:0       yes
2   0    0      2    2:2:2:0       yes
3   0    0      3    3:3:3:0       yes
4   0    0      0    0:0:0:0       yes
5   0    0      1    1:1:1:0       yes
6   0    0      2    2:2:2:0       yes
7   0    0      3    3:3:3:0       yes
```

Above is the output from a 4 core (8 if [hyper-threading][hyper-threading] is included) machine. All the cores are
on the same socket ([numa][numa] architecture). This gives rise to 4 distinct possibilities:
* two threads are bound on the same logical core
* two threads are bound on the same physical core, but different logical core (hyper-threading)
* two threads are bound on different physical cores, but same socket
* two threads are bound on different physical core, and different sockets

I wrote a small [program][code] to check the differences between each of these cases. The program is relatively simple,
and increments a counter for a fixed interval of time. (In this case `3 billion clock cycles`).

```cpp
template <typename T>
void increment_single_thread(T& counter)
{
   uint64_t end = __rdtsc() + interval;
   while (__rdtsc() < end)
      ++counter;
}
```
`__rdtsc` is from gcc's header `x86intrin.h`. In case of two threads, I look at two possibilities:
* counter is an atomic variable (`std::atomic<uint64_t>`)
* counter is a regular uint64_t protected by a `std::mutex`

On running the above code after setting the cores appropriately, I get the following results:

```
Single thread: 122,594,845
Single thread with std::mutex: 33,104,961
Single thread with spin lock is 62,786,379

Case1: Same logical core
Case2: Same physical core, different hyper-threads
Case3: Different physical core, same numa
Case4: Different physical core, different numa

             atomic        lock
Case1:   63,407,739  33,124,807
Case2:  116,827,188  17,899,622
Case3:   44,782,732   8,948,168
```

Observations for single thread:
* A single thread incremented the counter `122,594,845` times during this interval.
* A single thread with `std::mutex` lock only increments `33,104,961` times. That is about 4 times less. This was very
surprising to me. If there is no contention for the lock, I expected `std::mutex` lock/unlock to be fast. (I will try to
explore this in a separate blog post)
* With a spin lock, I got double the performance from std::mutex. This was expected. In case there is little/no
contention, I expected spin lock to beat std::mutex

Observations for two threads:
* On the same logical core, the performance of atomic counter is almost double the performance than std::mutex. Note
that on the same logical core, there is no contention at all. Each thread gets allocated a fixed amount of time before
it is prempted. The decrease in counter value for atomic is primarily due to context switching costs. I am not super
sure why context switching cost doesn't come into picture with the lock. (note that with lock on a single thread, the
performance decreased to almost 1/4th)
* When threads are bound on the same physical core, but different logical core, the atomic counter performance starts
matching the single thread counter performance! This is because both the threads are not getting pre-empted, and are
only paying the cost of using atomic counter. The locked version suffers because now there is a real contention for the
lock from both the threads.
* When the threads are bound to different physical cores, cache coherency affects start to come into play. Note that
each processor has its own L3 cache. When one thread writes to its cache, other copies of the same cache line get
invalidated, and as a result more trips to the main memory are required to synchronize the data between the two threads.
Lock performance suffers both from cache coherency issues as well as contention.
* My machine didn't have two cores on separate sockets, so unfortunately I don't have numbers from those. My guess is
that number is going to be even smaller due to QPI overhead.

The above **does not** mean that hyper-threading is the way to go! Following is from the [wiki page][hyper-threading]

```
Hyper-Threading can improve the performance of some MPI applications, but not all. Depending on the cluster
configuration and, most importantly, the nature of the application running on the cluster, performance gains can vary or
even be negative. The next step is to use performance tools to understand what areas contribute to performance gains and
what areas contribute to performance degradation.
```

[book]: https://www.amazon.com/C-Concurrency-Action-Practical-Multithreading/dp/1933988770/
[hyper-threading]: https://en.wikipedia.org/wiki/Hyper-threading
[numa]: https://en.wikipedia.org/wiki/Non-uniform_memory_access
[code]: https://github.com/skgbanga/Sandbox/blob/master/concurrency/blog/Counter.x.cpp
