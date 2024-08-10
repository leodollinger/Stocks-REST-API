class NotFound(Exception):
    def __init__(self, name: str):
        self.name = name


class PreconditionFailedName(Exception):
    def __init__(self, name: str):
        self.name = name


class PreconditionFailedAmount(Exception):
    def __init__(self, name: str):
        self.name = name
