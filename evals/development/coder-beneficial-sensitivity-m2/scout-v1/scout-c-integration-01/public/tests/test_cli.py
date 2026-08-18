from palette.css import render_css


def test_plain_name():
    assert render_css({"ink": "#000"}) == ":root {\n  --ink: #000;\n}\n"


# SCOUT-C-INT-R7: Add an actual test named test_renderer_rewrites_underscores asserting the exact CSS output for soft_blue.
