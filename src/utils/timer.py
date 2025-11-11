import time

class Timer:
    def __init__(self) -> None:
        self._start = None
        self._end = None
    
    def start(self):
        self._start = time.perf_counter()
    
    def stop(self):
        self._end = time.perf_counter()

    def reset(self):
        self._start = None
        self._end = None

    def get_elapsed(self):
        if self._start and self._end:
            return self._end - self._start
        return None

    def stop_get_elapsed_reset(self):
        self.stop()
        elapsed = self.get_elapsed()
        self.reset()
        return elapsed