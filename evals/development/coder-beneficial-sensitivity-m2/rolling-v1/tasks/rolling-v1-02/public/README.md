# triageboard

`triageboard` turns small support-ticket dictionaries into deterministic
routing cards. The policy used by every scored call is the exact `policy`
object in `fixtures/corridor.json`, except where a public test visibly copies
and extends that object.

## API — R1

The protected package initializer exports:

```python
from triageboard import route_ticket, route_tickets
```

`route_ticket(ticket, policy)` returns a newly allocated routed-ticket
dictionary. It must not mutate `ticket`, `policy`, or nested values belonging
to either argument.

`route_tickets(tickets, policy)` returns a newly allocated list of newly
allocated routed-ticket dictionaries and must not mutate its arguments.

## Ticket validation — R2

A ticket must be a dictionary with exactly these four keys:

```text
id
product
severity
tags
```

`id`, `product`, and `severity` must be strings that remain nonempty after
surrounding whitespace is removed. `tags` must be a list and every member
must be a string. Empty or whitespace-only tag strings are valid and are
discarded during output cleanup.

After normalization, `severity` must be a key in the policy’s
`priority_by_severity` dictionary.

Any violation above raises `ValueError`. Error wording is not scored. Policy
shape validation beyond the exact public policy is not scored.

## Normalization — R3

Strip surrounding whitespace from `id` but preserve its remaining spelling
and case.

Normalize `product` and `severity` by stripping surrounding whitespace and
then calling `lower()`.

After product normalization, perform exactly one lookup in the policy’s
`aliases` dictionary:

```python
canonical_product = aliases.get(normalized_product, normalized_product)
```

Do not repeatedly resolve alias targets. The public `phone -> ios -> mobile`
probe in `tests/test_public.py` must therefore produce `ios`, not `mobile`.

Normalize each tag by stripping surrounding whitespace and calling `lower()`.

## Queue selection — R4

Look up the canonical product in `policy["product_queues"]`. Use the mapped
queue when present; otherwise use `policy["default_queue"]`.

The public policy routes `billing` to `accounts`, routes `mobile` to `apps`,
and sends `other` to `general`.

## Priority — R5

The base priority is the integer at:

```python
policy["priority_by_severity"][normalized_severity]
```

After tags are normalized, membership of `policy["vip_tag"]` promotes the
ticket to priority `1`. Otherwise retain the base priority.

`escalated` is exactly `priority == 1`. Thus a high-severity ticket and a
normal-severity VIP ticket are both escalated, while an ordinary low-severity
ticket is not.

## Output — R6

Each routed ticket has exactly these six keys and types:

```text
id         string
product    string
queue      string
priority   integer
escalated  boolean
tags       list of strings
```

`tags` contains the normalized tags with empty strings removed, duplicates
removed, and the remaining strings sorted in ascending Python string order.

The complete expected corridor rows are public in
`fixtures/corridor.json["expected"]`.

## Batch routing — R7

`tickets` passed to `route_tickets` must be a list; otherwise raise
`ValueError`.

Route every member with `route_ticket`, then sort the result by the tuple:

```python
(priority, id)
```

Both components use ordinary ascending Python ordering.

## CLI — R8

From the repository root, the exact successful invocation is:

```text
python3 -m triageboard fixtures/corridor.json
```

The named UTF-8 JSON file is an object containing `policy`, `tickets`, and
`expected`. The CLI routes `tickets` with `policy`; `expected` is public
reference data and must not be used to produce the result.

On success, exit `0`, leave stderr empty, and write the routed list to stdout
using:

```python
json.dumps(
    result,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
) + "\n"
```

The exact stdout is:

```json
[{"escalated":true,"id":"T-03","priority":1,"product":"billing","queue":"accounts","tags":[]},{"escalated":true,"id":"T-20","priority":1,"product":"mobile","queue":"apps","tags":["beta","vip"]},{"escalated":false,"id":"T-11","priority":3,"product":"other","queue":"general","tags":["docs"]}]
```

followed by one newline.

The exact public failure invocation names the absent path
`fixtures/does-not-exist.json`. It must exit `2`, leave stdout empty, and
write a nonempty diagnostic to stderr. Diagnostic wording is not scored.
Ordinary argparse handling of malformed command lines is acceptable.
