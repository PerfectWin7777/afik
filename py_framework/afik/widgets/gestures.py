"""
Gesture detection and touch interaction widgets for Afik.
Provides GestureDetector, InkWell, and Dismissible.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from afik.core.constants import DismissDirection, HitTestBehavior
from afik.core.widget_base import Widget, _register_callback


class GestureDetector(Widget):
    """
    A widget that detects physical user gestures.
    Supports single tap, double tap, long press, and directional swipe gestures.
    
    Parameters:
        child: The widget subtree to monitor for touch gestures.
        on_tap: Invoked when a tap down, tap up has occurred.
        on_double_tap: Invoked when the user has tapped at the same location twice quickly.
        on_long_press: Invoked when a long-press gesture has been recognized.
        on_swipe_left: Invoked when a horizontal leftward swipe is detected.
        on_swipe_right: Invoked when a horizontal rightward swipe is detected.
        on_swipe_up: Invoked when a vertical upward swipe is detected.
        on_swipe_down: Invoked when a vertical downward swipe is detected.
        behavior: How this detector behaves during hit testing ('opaque', 'translucent', 'defer_to_child').
    """

    widget_type = "GestureDetector"

    def __init__(
        self,
        child: Widget,
        *,
        on_tap: Optional[Callable[[], None]] = None,
        on_double_tap: Optional[Callable[[], None]] = None,
        on_long_press: Optional[Callable[[], None]] = None,
        on_swipe_left: Optional[Callable[[], None]] = None,
        on_swipe_right: Optional[Callable[[], None]] = None,
        on_swipe_up: Optional[Callable[[], None]] = None,
        on_swipe_down: Optional[Callable[[], None]] = None,
        behavior: str = HitTestBehavior.OPAQUE,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            behavior=behavior,
            raw_props=raw_props,
        )
        self.children = [child]

        if on_tap is not None:
            self.callback_id = _register_callback(on_tap)
            self.props["on_tap_callback_id"] = self.callback_id

        if on_double_tap is not None:
            self.props["on_double_tap_callback_id"] = _register_callback(on_double_tap)

        if on_long_press is not None:
            self.props["on_long_press_callback_id"] = _register_callback(on_long_press)

        if on_swipe_left is not None:
            self.props["on_swipe_left_callback_id"] = _register_callback(on_swipe_left)

        if on_swipe_right is not None:
            self.props["on_swipe_right_callback_id"] = _register_callback(on_swipe_right)

        if on_swipe_up is not None:
            self.props["on_swipe_up_callback_id"] = _register_callback(on_swipe_up)

        if on_swipe_down is not None:
            self.props["on_swipe_down_callback_id"] = _register_callback(on_swipe_down)


class InkWell(Widget):
    """
    A rectangular area of a Material that responds to touch with a ripple animation.
    
    Parameters:
        child: The widget subtree inside the ripple area.
        on_tap: Invoked when tapped.
        on_double_tap: Invoked when double tapped.
        on_long_press: Invoked on long press.
        splash_color: The color of the splash ripple effect.
        highlight_color: The highlight color when pressed.
        border_radius: Corner radius clipping the ripple effect.
    """

    widget_type = "InkWell"

    def __init__(
        self,
        child: Widget,
        *,
        on_tap: Optional[Callable[[], None]] = None,
        on_double_tap: Optional[Callable[[], None]] = None,
        on_long_press: Optional[Callable[[], None]] = None,
        splash_color: Optional[str] = None,
        highlight_color: Optional[str] = None,
        border_radius: Optional[float] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            splash_color=splash_color,
            highlight_color=highlight_color,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        self.children = [child]

        if on_tap is not None:
            self.callback_id = _register_callback(on_tap)
            self.props["on_tap_callback_id"] = self.callback_id

        if on_double_tap is not None:
            self.props["on_double_tap_callback_id"] = _register_callback(on_double_tap)

        if on_long_press is not None:
            self.props["on_long_press_callback_id"] = _register_callback(on_long_press)


class Dismissible(Widget):
    """
    A widget that can be dismissed by swiping in the specified direction.
    Commonly used for swipe-to-delete items in lists or cart entries.
    
    Parameters:
        key: A unique string key identifying this dismissible item.
        child: The widget to swipe away.
        background: Optional background widget revealed during swipe.
        secondary_background: Optional background revealed when swiping in the opposite direction.
        direction: DismissDirection ('horizontal', 'end_to_start', 'start_to_end', 'vertical').
        on_dismissed: Callback invoked when the swipe completes: fn(direction: str).
    """

    widget_type = "Dismissible"

    def __init__(
        self,
        key: str,
        child: Widget,
        *,
        background: Optional[Widget] = None,
        secondary_background: Optional[Widget] = None,
        direction: str = DismissDirection.HORIZONTAL,
        on_dismissed: Optional[Callable[[str], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            key=str(key),
            direction=direction,
            raw_props=raw_props,
        )
        self.children = [child]

        if background is not None:
            background.props["slot"] = "background"
            self.children.append(background)

        if secondary_background is not None:
            secondary_background.props["slot"] = "secondary_background"
            self.children.append(secondary_background)

        if on_dismissed is not None:
            self.callback_id = _register_callback(on_dismissed)
