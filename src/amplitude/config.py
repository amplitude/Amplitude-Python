from amplitude.storage import Storage


class Config:

    def __init__(self):
        self.storage_provider = Storage()


DEFAULT_CONFIG = Config()
