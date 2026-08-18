"""Render color mappings as CSS custom properties."""


def render_css(colors, prefix=None):
    lines = [":root {"]
    for name, value in colors.items():
        # SCOUT-C-INT-R2: In render_css, convert every underscore in a color name to a hyphen before forming the CSS variable name.
        variable = f"{prefix}-{name}" if prefix else name
        lines.append(f"  --{variable}: {value};")
    lines.append("}")
    return "\n".join(lines) + "\n"
