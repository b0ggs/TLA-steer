"""Small workflow helpers used by the evaluation fixture."""


def merge_context(base, overlay):
    result = dict(base)
    result.update(overlay)
    return result


def execution_waves(steps):
    raise NotImplementedError("dependency scheduling is not available")
