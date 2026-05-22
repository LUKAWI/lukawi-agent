"""TUI themes — visual styling configurations."""

from lukawi.tui.themes.default import DarkTheme, LightTheme, OLEDTheme
from lukawi.tui.themes.registry import ThemeRegistry

# Backward-compatible alias
DefaultTheme = DarkTheme


def create_default_registry() -> ThemeRegistry:
    """Create a ThemeRegistry with all three themes pre-registered, dark active."""
    registry = ThemeRegistry()
    registry.register(DarkTheme())
    registry.register(LightTheme())
    registry.register(OLEDTheme())
    registry.use("lukawi-dark")
    return registry


__all__ = [
    "DarkTheme",
    "DefaultTheme",
    "LightTheme",
    "OLEDTheme",
    "ThemeRegistry",
    "create_default_registry",
]
