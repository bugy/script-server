import threading


class IdGenerator:
    def __init__(self, existing_ids):
        self._next_id = self._calc_next_id(existing_ids)
        self.lock = threading.Lock()

    @staticmethod
    def _calc_next_id(existing_ids):
        max_id = 0
        for existing_id in existing_ids:
            try:
                numeric_id = int(existing_id)
                if numeric_id > max_id:
                    max_id = numeric_id
            except ValueError:
                continue
        return max_id + 1

    def next_id(self):
        with self.lock:
            id = self._next_id
            self._next_id += 1

        return str(id)
