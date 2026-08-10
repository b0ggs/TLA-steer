# Environment template command

Update `solution.py` so that it satisfies all of the following requirements:

- Expand ${NAME} placeholders in stdin from the process environment, allowing letters, digits, and underscores after an initial letter or underscore.
- Interpret $$ as one literal dollar sign and leave an undefined placeholder unchanged by default.
- With --strict, report every undefined variable on stderr and exit 2 without writing partial stdout.

Regression constraint: Text containing no dollar sign must pass through byte-for-byte.

