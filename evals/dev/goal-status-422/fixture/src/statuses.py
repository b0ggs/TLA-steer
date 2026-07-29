"""HTTP status selection for application errors."""


STATUS_BY_ERROR = {
    "validation_error": 400,
    "not_found": 404,
    "conflict": 409,
}


def status_for_error(error_kind):
    return STATUS_BY_ERROR.get(error_kind, 500)
