"""
Animation and transition widgets for PyFlutter.
Provides Hero, AnimatedContainer, AnimatedOpacity, AnimatedScale,
AnimatedRotation, AnimatedAlign, and AnimatedCrossFade.
All implicit animations run at native 60/120 FPS on the device GPU.
"""

from __future__ import annotations

from typing import Any, Optional

from pyflutter.core.constants import Alignment, Curves
from pyflutter.core.style import Duration
from pyflutter.core.widget_base import Widget


class Hero(Widget):
    """
    A widget that marks its child as being a candidate for shared-element
    screen-to-screen hero animations.
    
    When navigating between screens with matching tags, Flutter automatically
    flies and scales the widget smoothly across the route transition.
    
    Parameters:
        tag: A unique string identifier shared across source and destination screens.
        child: The widget to animate between screens.
    """

    widget_type = "Hero"

    def __init__(
        self,
        tag: str,
        child: Widget,
        *,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            tag=str(tag),
            raw_props=raw_props,
        )
        self.children = [child]


class AnimatedContainer(Widget):
    """
    An animated version of Container that smoothly transitions its properties
    (width, height, color, border_radius, padding, margin) over a given duration.
    
    Parameters:
        child: Optional child widget.
        width: Box width in logical pixels.
        height: Box height in logical pixels.
        color: Background color hex string (e.g. '#1877F2').
        border_radius: Rounded corner radius in pixels.
        padding: Internal padding in pixels.
        margin: External margin in pixels.
        duration: Animation duration (default: Duration(milliseconds=300)).
        curve: Animation easing curve (Curves.EASE_IN_OUT, Curves.BOUNCE_OUT, etc.).
    """

    widget_type = "AnimatedContainer"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        color: Optional[str] = None,
        border_radius: Optional[float] = None,
        padding: Optional[float] = None,
        margin: Optional[float] = None,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            width=width,
            height=height,
            color=color,
            border_radius=border_radius,
            padding=padding,
            margin=margin,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]


class AnimatedOpacity(Widget):
    """
    Animates the opacity of its child over a given duration.
    
    Parameters:
        child: The widget to fade in or out.
        opacity: Opacity between 0.0 (fully transparent) and 1.0 (fully visible).
        duration: Animation duration (default: Duration(milliseconds=300)).
        curve: Animation easing curve (default: Curves.EASE_IN_OUT).
    """

    widget_type = "AnimatedOpacity"

    def __init__(
        self,
        child: Widget,
        *,
        opacity: float = 1.0,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            opacity=opacity,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        self.children = [child]


class AnimatedScale(Widget):
    """
    Animates the scale of its child over a given duration.
    
    Parameters:
        child: The widget to scale.
        scale: Scale factor (e.g. 1.0 for original size, 1.2 for enlarged, 0.0 for collapsed).
        duration: Animation duration (default: Duration(milliseconds=300)).
        curve: Animation easing curve.
    """

    widget_type = "AnimatedScale"

    def __init__(
        self,
        child: Widget,
        *,
        scale: float = 1.0,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            scale=scale,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        self.children = [child]


class AnimatedRotation(Widget):
    """
    Animates the rotation of its child over a given duration.
    
    Parameters:
        child: The widget to rotate.
        turns: Rotation in turns (1.0 = 360 degrees, 0.5 = 180 degrees, 0.25 = 90 degrees).
        duration: Animation duration (default: Duration(milliseconds=300)).
        curve: Animation easing curve.
    """

    widget_type = "AnimatedRotation"

    def __init__(
        self,
        child: Widget,
        *,
        turns: float = 0.0,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            turns=turns,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        self.children = [child]


class AnimatedAlign(Widget):
    """
    Animates the alignment of its child over a given duration.
    
    Parameters:
        child: The widget to position and animate.
        alignment: Target alignment (Alignment.TOP_LEFT, Alignment.CENTER, Alignment.BOTTOM_RIGHT, etc.).
        duration: Animation duration (default: Duration(milliseconds=300)).
        curve: Animation easing curve.
    """

    widget_type = "AnimatedAlign"

    def __init__(
        self,
        child: Widget,
        *,
        alignment: str = Alignment.CENTER,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            alignment=alignment,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        self.children = [child]


class AnimatedCrossFade(Widget):
    """
    Cross-fades between two children over a given duration.
    
    Parameters:
        first_child: The first child widget.
        second_child: The second child widget.
        show_first: Whether to show the first child (True) or the second (False).
        duration: Cross-fade animation duration (default: Duration(milliseconds=300)).
        curve: Animation curve.
    """

    widget_type = "AnimatedCrossFade"

    def __init__(
        self,
        first_child: Widget,
        second_child: Widget,
        *,
        show_first: bool = True,
        duration: Optional[Duration] = None,
        curve: str = Curves.EASE_IN_OUT,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        d = duration if duration is not None else Duration(milliseconds=300)
        super().__init__(
            show_first=show_first,
            duration_ms=d.in_milliseconds,
            curve=curve,
            raw_props=raw_props,
        )
        first_child.props["slot"] = "first_child"
        second_child.props["slot"] = "second_child"
        self.children = [first_child, second_child]
