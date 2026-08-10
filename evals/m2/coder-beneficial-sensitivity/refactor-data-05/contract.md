# Schema-driven row coercion

Update `solution.py` so that it satisfies all of the following requirements:

- Implement coerce_rows(rows, schema), where each schema value is (converter, default), returning new dictionaries containing schema fields only.
- Apply each converter to present non-None values; use a deep copy of the default for missing or None values.
- On converter failure, use the default and append (row_index, field, original_value) to a separate errors list in row and schema order.

Regression constraint: Return (converted_rows, errors), do not mutate inputs, and handle empty rows or schema.

