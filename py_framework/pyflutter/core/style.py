"""
PyFlutter Material 3 Styling and Typography System.
Provides native Flutter-identical abstractions for ThemeData, ColorScheme,
TextStyle, ThemeMode, and Duration with full IDE auto-completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


class Duration:
    """
    A span of time, identically matching Flutter's Duration class.
    
    Usage:
        Duration(seconds=4)
        Duration(milliseconds=500)
        Duration(minutes=1, seconds=30)
    """

    def __init__(
        self,
        *,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: float | int = 0,
        milliseconds: int = 0,
        microseconds: int = 0,
    ):
        self._microseconds = int(
            days * 86_400_000_000
            + hours * 3_600_000_000
            + minutes * 60_000_000
            + seconds * 1_000_000
            + milliseconds * 1_000
            + microseconds
        )

    @property
    def in_milliseconds(self) -> int:
        """Total duration expressed in whole milliseconds."""
        return self._microseconds // 1_000

    @property
    def in_seconds(self) -> float:
        """Total duration expressed in fractional seconds."""
        return self._microseconds / 1_000_000

    def __repr__(self) -> str:
        return f"Duration({self.in_milliseconds}ms)"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self._microseconds == other._microseconds
        return False


class FontStyle:
    """Whether font glyphs are italicized or upright."""
    NORMAL = "normal"
    ITALIC = "italic"


class TextDecoration:
    """A linear decoration drawn near or through text."""
    NONE = "none"
    UNDERLINE = "underline"
    LINE_THROUGH = "lineThrough"
    OVERLINE = "overline"


class TextOverflow:
    """How overflowing text should be handled."""
    CLIP = "clip"
    FADE = "fade"
    ELLIPSIS = "ellipsis"


class ThemeMode:
    """Operating system brightness adaptation mode."""
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class TextTheme:
    """
    Standard Material 3 Typography Scale identifiers.
    Enables IDE autocompletion for all 15 standardized Material 3 typography roles.
    """
    DISPLAY_LARGE = "displayLarge"
    DISPLAY_MEDIUM = "displayMedium"
    DISPLAY_SMALL = "displaySmall"

    HEADLINE_LARGE = "headlineLarge"
    HEADLINE_MEDIUM = "headlineMedium"
    HEADLINE_SMALL = "headlineSmall"

    TITLE_LARGE = "titleLarge"
    TITLE_MEDIUM = "titleMedium"
    TITLE_SMALL = "titleSmall"

    BODY_LARGE = "bodyLarge"
    BODY_MEDIUM = "bodyMedium"
    BODY_SMALL = "bodySmall"

    LABEL_LARGE = "labelLarge"
    LABEL_MEDIUM = "labelMedium"
    LABEL_SMALL = "labelSmall"


@dataclass
class TextStyle:
    """
    An immutable style description for a run of text, matching Flutter's TextStyle.
    
    Usage:
        style = TextStyle(theme_style="headlineLarge", color=Colors.PRIMARY)
        style = TextStyle(font_size=18, font_weight="bold", decoration="underline")
    """
    color: Optional[str] = None
    font_size: Optional[float | int] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None
    font_family: Optional[str] = None
    letter_spacing: Optional[float] = None
    word_spacing: Optional[float] = None
    height: Optional[float] = None
    decoration: Optional[str] = None
    decoration_color: Optional[str] = None
    theme_style: Optional[str] = None

    def copy_with(
        self,
        *,
        color: Optional[str] = None,
        font_size: Optional[float | int] = None,
        font_weight: Optional[str] = None,
        font_style: Optional[str] = None,
        font_family: Optional[str] = None,
        letter_spacing: Optional[float] = None,
        word_spacing: Optional[float] = None,
        height: Optional[float] = None,
        decoration: Optional[str] = None,
        decoration_color: Optional[str] = None,
        theme_style: Optional[str] = None,
    ) -> TextStyle:
        """Returns a new copy of this TextStyle with the specified fields replaced."""
        return TextStyle(
            color=color if color is not None else self.color,
            font_size=font_size if font_size is not None else self.font_size,
            font_weight=font_weight if font_weight is not None else self.font_weight,
            font_style=font_style if font_style is not None else self.font_style,
            font_family=font_family if font_family is not None else self.font_family,
            letter_spacing=letter_spacing if letter_spacing is not None else self.letter_spacing,
            word_spacing=word_spacing if word_spacing is not None else self.word_spacing,
            height=height if height is not None else self.height,
            decoration=decoration if decoration is not None else self.decoration,
            decoration_color=decoration_color if decoration_color is not None else self.decoration_color,
            theme_style=theme_style if theme_style is not None else self.theme_style,
        )

    def to_props(self) -> dict[str, str]:
        """Serializes non-null properties into IR map props."""
        props: dict[str, str] = {}
        if self.color is not None:
            props["color"] = str(self.color)
        if self.font_size is not None:
            props["font_size"] = str(self.font_size)
        if self.font_weight is not None:
            props["font_weight"] = str(self.font_weight)
        if self.font_style is not None:
            props["font_style"] = str(self.font_style)
        if self.font_family is not None:
            props["font_family"] = str(self.font_family)
        if self.letter_spacing is not None:
            props["letter_spacing"] = str(self.letter_spacing)
        if self.word_spacing is not None:
            props["word_spacing"] = str(self.word_spacing)
        if self.height is not None:
            props["height"] = str(self.height)
        if self.decoration is not None:
            props["decoration"] = str(self.decoration)
        if self.decoration_color is not None:
            props["decoration_color"] = str(self.decoration_color)
        if self.theme_style is not None:
            props["theme_style"] = str(self.theme_style)
        return props


class ColorScheme:
    """
    A set of 30 harmonious Material 3 colors based on the Material spec.
    Can be dynamically generated using ColorScheme.from_seed(seed_color="#1877F2").
    """

    def __init__(
        self,
        *,
        primary: Optional[str] = None,
        on_primary: Optional[str] = None,
        primary_container: Optional[str] = None,
        on_primary_container: Optional[str] = None,
        secondary: Optional[str] = None,
        on_secondary: Optional[str] = None,
        surface: Optional[str] = None,
        on_surface: Optional[str] = None,
        error: Optional[str] = None,
        on_error: Optional[str] = None,
        brightness: str = "light",
        seed_color: Optional[str] = None,
    ):
        self.primary = primary
        self.on_primary = on_primary
        self.primary_container = primary_container
        self.on_primary_container = on_primary_container
        self.secondary = secondary
        self.on_secondary = on_secondary
        self.surface = surface
        self.on_surface = on_surface
        self.error = error
        self.on_error = on_error
        self.brightness = brightness
        self.seed_color = seed_color

    @classmethod
    def from_seed(
        cls,
        seed_color: str,
        *,
        brightness: str = "light",
        primary: Optional[str] = None,
        surface: Optional[str] = None,
    ) -> ColorScheme:
        """
        Generates a dynamic 30-color Material 3 harmonic palette from a single seed color.
        Identical to Flutter's `ColorScheme.fromSeed(seedColor: Color)`.
        """
        return cls(
            seed_color=seed_color,
            brightness=brightness,
            primary=primary or seed_color,
            surface=surface,
        )

    def to_props(self) -> dict[str, str]:
        props: dict[str, str] = {"brightness": self.brightness}
        if self.seed_color is not None:
            props["seed_color"] = str(self.seed_color)
        if self.primary is not None:
            props["primary"] = str(self.primary)
        if self.surface is not None:
            props["surface"] = str(self.surface)
        if self.secondary is not None:
            props["secondary"] = str(self.secondary)
        if self.error is not None:
            props["error"] = str(self.error)
        return props


class ThemeData:
    """
    Defines the overall visual theme of a PyFlutter application or sub-tree.
    Identical to Flutter's ThemeData.
    """

    def __init__(
        self,
        *,
        use_material3: bool = True,
        color_scheme: Optional[ColorScheme] = None,
        scaffold_background_color: Optional[str] = None,
        primary_color: Optional[str] = None,
        card_color: Optional[str] = None,
        app_bar_theme: Optional[dict[str, Any]] = None,
        card_theme: Optional[dict[str, Any]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        self.use_material3 = use_material3
        self.color_scheme = color_scheme
        self.scaffold_background_color = scaffold_background_color
        self.primary_color = primary_color
        self.card_color = card_color
        self.app_bar_theme = app_bar_theme or {}
        self.card_theme = card_theme or {}
        self.raw_props = raw_props or {}

    def to_props(self, prefix: str = "theme_") -> dict[str, str]:
        props: dict[str, str] = {
            f"{prefix}use_material3": "true" if self.use_material3 else "false"
        }
        if self.color_scheme is not None:
            for k, v in self.color_scheme.to_props().items():
                props[f"{prefix}color_scheme_{k}"] = str(v)
            if self.color_scheme.seed_color:
                props[f"{prefix}seed_color"] = str(self.color_scheme.seed_color)

        if self.scaffold_background_color is not None:
            props[f"{prefix}scaffold_background_color"] = str(self.scaffold_background_color)
        if self.primary_color is not None:
            props[f"{prefix}primary_color"] = str(self.primary_color)
        if self.card_color is not None:
            props[f"{prefix}card_color"] = str(self.card_color)

        for k, v in self.raw_props.items():
            props[f"{prefix}{k}"] = str(v)

        return props
