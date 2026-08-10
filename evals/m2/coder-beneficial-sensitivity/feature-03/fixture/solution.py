class RateLimiter:
    def __init__(self, limit, window):
        self.limit=limit
    def allow(self, key, now):
        return True

