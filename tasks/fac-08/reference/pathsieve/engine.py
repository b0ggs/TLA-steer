"""The Sieve engine: applies an ordered list of rules to paths."""

from .patterns import Rule, compile_pattern


class Sieve:
    """An ordered rule set that decides which paths are excluded."""

    def __init__(self, patterns, ignore_case=False):
        self.rules = []
        for item in patterns:
            if isinstance(item, Rule):
                self.rules.append(item)
            else:
                self.rules.append(compile_pattern(item))
        self.ignore_case = ignore_case

    def decide(self, path):
        """Decide whether *path* is excluded.

        The last matching rule wins. When that rule is a negation
        (leading ``!``) the path is re-included; otherwise it is
        excluded. Paths matching no rule stay included.

        Returns True when the path is excluded by the rule set and
        False when it survives filtering.
        """
        verdict = False
        for rule in self.rules:
            if rule.matches(path, self.ignore_case):
                verdict = not rule.negated
        return verdict

    def excludes(self, path):
        """Alias for :meth:`decide`."""
        return self.decide(path)
