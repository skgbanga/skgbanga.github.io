// Compile this in infra directory
// g++ -O3 -I /path/to/boost/ -lpthread -lrt -Wno-deprecated-declarations
// spsc.cpp

#include <boost/accumulators/accumulators.hpp>
#include <boost/accumulators/statistics.hpp>
#include <boost/lockfree/spsc_queue.hpp>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <pthread.h>
#include <thread>
#include <vector>

using namespace std::chrono_literals;  // NOLINT
using namespace boost::accumulators;   // NOLINT

// using Clock = std::chrono::high_resolution_clock;
// using Clock = std::chrono::system_clock;

// using TimePoint = Clock::time_point;
using TimePoint = uint64_t;

inline uint64_t rdtsc(void) { return __builtin_ia32_rdtsc(); }

inline uint64_t rdtsc_begin_profile(void) {
  uint32_t hi, lo;
  asm volatile(
      "CPUID\n\t" /*serialize*/
      "RDTSC\n\t" /*read the clock*/
      "mov %%edx, %0\n\t"
      "mov %%eax, %1\n\t"
      : "=r"(hi), "=r"(lo)::"%rax", "%rbx", "%rcx", "%rdx");

  return (static_cast<uint64_t>(lo) | (static_cast<uint64_t>(hi) << 32));
}

inline uint64_t rdtsc_end_profile(void) {
  uint32_t hi, lo;
  asm volatile(
      "RDTSCP\n\t" /*read the clock*/
      "mov %%edx, %0\n\t"
      "mov %%eax, %1\n\t"
      "CPUID\n\t"
      : "=r"(hi), "=r"(lo)::"%rax", "%rbx", "%rcx", "%rdx");

  return (static_cast<uint64_t>(lo) | (static_cast<uint64_t>(hi) << 32));
}

TimePoint system_time() {
  struct timespec tv;
  clock_gettime(CLOCK_REALTIME, &tv);
  return tv.tv_sec * std::pow(10, 9) + tv.tv_nsec;
}

auto get_system_time_and_tick() {
  TimePoint tp;
  uint64_t ticks;

  static const int tries = 5;

  int64_t diff = std::numeric_limits<int64_t>::max();

  for (int i = 0; i < tries; ++i) {
    uint64_t start_ticks = rdtsc();

    TimePoint sample_tp = system_time();
    uint64_t sample_ticks = rdtsc();

    // make sure there is no context switch between getSystemTime() and rdtsc()
    if ((int64_t)(sample_ticks - start_ticks) < diff) {
      tp = sample_tp;
      ticks = sample_ticks;
      diff = sample_ticks - start_ticks;
    }
  }

  return std::pair(tp, ticks);
}

double nanos_per_tick() {
  using namespace std::chrono_literals;  // NOLINT
  auto[start_time, start_ticks] = get_system_time_and_tick();
  std::this_thread::sleep_for(1us);
  auto[end_time, end_ticks] = get_system_time_and_tick();

  return 1.0 * (end_time - start_time) / (end_ticks - start_ticks);
}

struct Data {
  TimePoint enter;
  TimePoint exit;
};

boost::lockfree::spsc_queue<Data, boost::lockfree::capacity<1024>>
    communication_queue;
boost::lockfree::spsc_queue<Data, boost::lockfree::capacity<1024>>
    logging_queue;

std::condition_variable cv;
std::mutex m;
int i = 0;

void set_name_affinity(std::thread& t, std::string name, int core) {  // NOLINT
  auto id = t.native_handle();

  auto err = pthread_setname_np(id, name.c_str());
  if (err != 0) {
    perror("Error setting name of the thread");
    std::exit(EXIT_FAILURE);
  }

  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core, &cpuset);

  err = pthread_setaffinity_np(id, sizeof(cpu_set_t), &cpuset);
  if (err != 0) {
    perror("Error setting affinity of the thread");
    std::exit(EXIT_FAILURE);
  }
}

int main() {
  const int iterations = 100'000;
  auto producer = []() {
    {
      std::unique_lock<std::mutex> lk(m);
      cv.wait(lk, [] { return i == 1; });
    }

    Data data;
    for (int i = 0; i < iterations; ++i) {
      // sleep for some time so that consumer thread can consume the packet
      std::this_thread::sleep_for(5us);

      data.enter = rdtsc_begin_profile();
      // data.enter = Clock::now();
      while (!communication_queue.push(data)) {
      }
    }
  };

  auto consumer = []() {
    {
      std::unique_lock<std::mutex> lk(m);
      cv.wait(lk, [] { return i == 1; });
    }

    Data data;
    for (int i = 0; i < iterations; ++i) {
      // If there is more than one packet available in the queue to be read
      // bomb out
      auto r = communication_queue.read_available();
      if (r > 1) {
        std::cerr << "Number of elements in queue " << r << std::endl;
        std::exit(EXIT_FAILURE);
      }

      while (!communication_queue.pop(data)) {
      }
      // data.exit = Clock::now();
      data.exit = rdtsc_end_profile();

      // log the data
      while (!logging_queue.push(data)) {
      }
    }
  };

  auto logger = []() {
    auto multiplier = nanos_per_tick();
    uint64_t tick1 = rdtsc_begin_profile();
    uint64_t tick2 = rdtsc_end_profile();
    auto overhead_ticks = tick2 - tick1;

    std::vector<uint64_t> samples;
    accumulator_set<uint64_t, features<tag::mean, tag::median, tag::variance>>
        accumulator;
    Data data;
    for (int i = 0; i < iterations; ++i) {
      while (!logging_queue.pop(data)) {
      }
      auto delta = data.exit - data.enter - overhead_ticks;

      samples.push_back(delta * multiplier);
      // samples.push_back(static_cast<std::chrono::nanoseconds>(delta).count());
    }

    for (auto sample : samples) {
      accumulator(sample);
    }
    std::cout << "Total number of samples: " << samples.size() << std::endl;
    std::cout << "Mean: " << mean(accumulator) << std::endl;
    std::cout << "Median: " << median(accumulator) << std::endl;
    std::cout << "Variance: " << variance(accumulator) << std::endl;
  };

  std::thread producer_thread(producer);
  std::thread consumer_thread(consumer);
  std::thread logger_thread(logger);

  set_name_affinity(producer_thread, "producer", 6);
  set_name_affinity(consumer_thread, "consumer", 7);
  set_name_affinity(logger_thread, "logger", 8);

  std::this_thread::sleep_for(2s);
  // both consumer and producer are waiting on the condition variable
  {
    std::lock_guard<std::mutex> lk(m);
    i = 1;
  }
  cv.notify_all();

  producer_thread.join();
  consumer_thread.join();
  logger_thread.join();
}
