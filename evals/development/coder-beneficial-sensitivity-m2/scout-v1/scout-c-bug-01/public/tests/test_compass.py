from starmap.compass import direction_name


def test_east():
    assert direction_name(90) == "E"


# SCOUT-C-BUG-R6: Add an actual two-line test named test_zero_degrees_is_north whose body is assert direction_name(0) == "N".
