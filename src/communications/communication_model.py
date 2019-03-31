class File:
    def __init__(self, filename, content=None, content_type=None, path=None) -> None:
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.path = path
