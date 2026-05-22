"""Theme registry — runtime theme discovery and switching."""

from textual.theme import Theme


class ThemeRegistry:
    """Manages available themes and provides runtime switching."""

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._current: str | None = None

    def register(self, theme: Theme) -> None:
        """Register a theme by its name. Silently replaces if already registered."""
        self._themes[theme.name] = theme

    def get(self, name: str) -> Theme:
        """Retrieve a registered theme by name. Raises KeyError if not found."""
        if name not in self._themes:
            raise KeyError(f"Theme {name!r} is not registered. Available: {self.list_themes()}")
        return self._themes[name]

    def list_themes(self) -> list[str]:
        """Return sorted list of registered theme names."""
        return sorted(self._themes)

    def use(self, name: str) -> Theme:
        """Switch to a registered theme and update current. Returns the theme."""
        theme = self.get(name)
        self._current = name
        return theme

    @property
    def current(self) -> Theme | None:
        """Return the currently selected theme, or None if none selected."""
        if self._current is None:
            return None
        return self._themes.get(self._current)

    @property
    def current_name(self) -> str | None:
        """Return the name of the currently selected theme, or None."""
        return self._current
