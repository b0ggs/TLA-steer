"""Frequency counting for tokenized words."""


def count_words(words):
    """Return a dict mapping each word to the number of times it occurs."""
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


def merge_counts(*mappings):
    """Merge several word-count mappings into one dict."""
    merged = {}
    for mapping in mappings:
        for word, count in mapping.items():
            merged[word] = merged.get(word, 0) + count
    return merged
