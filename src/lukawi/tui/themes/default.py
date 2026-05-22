"""Theme definitions for Lukawi TUI — dark, light, and AMOLED variants."""

from textual.theme import Theme


class DarkTheme(Theme):
    """Lukawi default dark theme — muted blue, sage green, amber accents."""

    def __init__(self) -> None:
        super().__init__(
            name="lukawi-dark",
            primary="#6C8EBF",       # Muted blue
            secondary="#82B366",     # Sage green
            accent="#D79B00",        # Amber/gold
            success="#82B366",       # Green
            warning="#D79B00",       # Amber
            error="#B85450",         # Muted red
            surface="#1E1E2E",       # Dark navy
            background="#181825",    # Deeper dark
            panel="#252536",         # Slightly lighter
            foreground="#CDD6F4",    # Light lavender
            dark=True,
            variables={
                "foreground-muted": "#6C7086",   # Muted text
            },
        )


class LightTheme(Theme):
    """Lukawi light theme — soft blue, green, and gold on white."""

    def __init__(self) -> None:
        super().__init__(
            name="lukawi-light",
            primary="#4A6FA5",       # Muted blue
            secondary="#5A9E4B",     # Sage green
            accent="#B8860B",        # Dark goldenrod
            success="#5A9E4B",       # Green
            warning="#B8860B",       # Amber
            error="#C0392B",         # Red
            surface="#F5F5F5",       # Off-white
            background="#FFFFFF",    # Pure white
            panel="#E8E8E8",         # Light grey
            foreground="#2C3E50",    # Dark slate
            dark=False,
            variables={
                "foreground-muted": "#7F8C8D",   # Muted grey
            },
        )


class OLEDTheme(Theme):
    """Lukawi AMOLED theme — pure black background for OLED screens."""

    def __init__(self) -> None:
        super().__init__(
            name="lukawi-amoled",
            primary="#569CD6",       # VS Code blue
            secondary="#6A9955",     # Muted green
            accent="#DCDCAA",        # Light gold
            success="#6A9955",       # Green
            warning="#DCDCAA",       # Gold
            error="#F44747",         # Bright red
            surface="#0D0D0D",       # Near-black
            background="#000000",    # Pure black
            panel="#1A1A1A",         # Slightly lighter black
            foreground="#D4D4D4",    # Light grey
            dark=True,
            variables={
                "foreground-muted": "#808080",   # Muted grey
            },
        )


# Backward-compatible alias
DefaultTheme = DarkTheme
