from concurrent.futures import ThreadPoolExecutor


def create_workers_pool():
    executor = ThreadPoolExecutor(max_workers=5)
    return executor
