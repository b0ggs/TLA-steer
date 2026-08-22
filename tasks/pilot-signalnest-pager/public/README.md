# SignalNest

SignalNest is a small, standard-library-only route alias resolver used by a
fictional notification service.

```python
from signalnest import resolve_route

assert resolve_route("email") == "standard"
```

The quick smoke suite uses `python3 -m unittest`. Maintainer release checks and
generated-file policy are documented in `docs/development.md`.
