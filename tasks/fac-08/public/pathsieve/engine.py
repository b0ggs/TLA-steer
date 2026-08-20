"""The Sieve engine: applies an ordered list of rules to paths."""

from .patterns import Rule, compile_pattern


class Sieve:
    """An ordered rule set that decides which paths are excluded."""

    def __init__(self, patterns, ignore_case=True):
        self.rules = []
        for item in patterns:
            if isinstance(item, Rule):
                self.rules.append(item)
            else:
                self.rules.append(compile_pattern(item))
        self.ignore_case = ignore_case

    def decide(self, path):
        """Decide whether *path* is excluded.

        Returns True when the path is excluded by the rule set and
        False when it survives filtering.
        """
        for rule in self.rules:
            if rule.matches(path, self.ignore_case):
                return True
        return False

    def excludes(self, path):
        """Alias for :meth:`decide`."""
        return self.decide(path)
