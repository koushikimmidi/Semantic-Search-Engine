import time

from backend.profiling import PerformanceProfiler


def main():

    profiler = PerformanceProfiler()

    profiler.start("Loading")

    time.sleep(1)

    profiler.stop("Loading")

    profiler.start("Encoding")

    time.sleep(0.5)

    profiler.stop("Encoding")

    profiler.start("Searching")

    time.sleep(0.3)

    profiler.stop("Searching")

    profiler.report()


if __name__ == "__main__":
    main()