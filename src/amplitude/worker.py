from concurrent.futures import ThreadPoolExecutor


class Response:
    pass


def create_workers_pool():
    executor = ThreadPoolExecutor(max_workers=5)
    return executor
