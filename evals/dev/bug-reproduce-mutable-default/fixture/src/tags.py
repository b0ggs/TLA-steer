"""Tag merging helpers."""


def merge_tags(new_tags, accumulated=[]):
    accumulated.extend(new_tags)
    return accumulated
