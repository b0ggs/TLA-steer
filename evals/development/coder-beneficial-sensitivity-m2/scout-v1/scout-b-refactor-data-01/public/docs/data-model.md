# Inventory data model

Rows carry a SKU, quantity, and zero or more labels.

## Pending migration note

R7 — Add a `## Frozen row model` section to `docs/data-model.md` containing the sentences `InventoryRow instances are immutable.` and `Legacy input may use qty; serialized output uses the configured quantity key.`
