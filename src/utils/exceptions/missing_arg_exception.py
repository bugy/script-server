class MissingArgumentException(Exception):
    def __init__(self, message, arg_name) -> None:
        super().__init__(message)

        self.arg_name = arg_name
