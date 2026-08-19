"""Build volunteer access-badge manifests."""


class BadgeManifestError(ValueError):
    pass


def build_manifest(
    attendees: list[object],
    policy: dict[str, object],
) -> list[dict[str, object]]:
    raise NotImplementedError
