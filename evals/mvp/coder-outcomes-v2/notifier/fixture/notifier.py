"""Small notification helpers used by the evaluation fixture."""


def render(template, values):
    return template.format_map(values)


def due_notification_ids(records, now):
    return [record["id"] for record in records
            if record["scheduled_at"] <= now]


def build_deliveries(event, subscriptions, templates):
    raise NotImplementedError("delivery integrations are not configured")
