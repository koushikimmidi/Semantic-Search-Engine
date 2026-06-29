import time


class PerformanceProfiler:

    def __init__(self):

        self.timings = {}

    def start(self, operation):

        self.timings[operation] = time.perf_counter()

    def stop(self, operation):

        if operation not in self.timings:
            return 0

        elapsed = time.perf_counter() - self.timings[operation]

        self.timings[operation] = elapsed

        return elapsed

    def report(self):

        print("\n" + "=" * 60)
        print("PERFORMANCE REPORT")
        print("=" * 60)

        total = 0

        for operation, elapsed in self.timings.items():

            print(f"{operation:<20} : {elapsed:.6f} sec")

            total += elapsed

        print("-" * 60)
        print(f"{'Total':<20} : {total:.6f} sec")