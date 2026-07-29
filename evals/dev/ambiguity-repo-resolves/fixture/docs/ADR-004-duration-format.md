# ADR-004: Compact duration format

Status: Accepted

Duration displays below 60 minutes remain `<minutes> min`.

Duration displays of 60 minutes or more use `<hours>h <minutes>m`. The minutes
component is always two digits.

Examples:

- 59 minutes: `59 min`
- 60 minutes: `1h 00m`
- 65 minutes: `1h 05m`
- 125 minutes: `2h 05m`
