"""
PyFlutter Widget Collection.
Fully-typed, documented widgets with complete IDE hover, autocomplete, and docstrings.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

from pyflutter.core.widget_base import Widget, _register_callback, QtSignal
from pyflutter.core.constants import (
    Axis,
    BoxFit,
    FlexFit,
    WrapAlignment,
    MainAxisSize,
    FloatingActionButtonLocation,
    ScrollPhysics,
)
from pyflutter.core.style import TextStyle, ThemeData, ColorScheme
from pyflutter.core.form import (
    Form,
    FormKey,
    TextEditingController,
    Validators,
    InputBorder,
    OutlineInputBorder,
    UnderlineInputBorder,
)
from pyflutter.widgets.gestures import (
    GestureDetector,
    InkWell,
    Dismissible,
)
from pyflutter.widgets.animations import (
    Hero,
    AnimatedContainer,
    AnimatedOpacity,
    AnimatedScale,
    AnimatedRotation,
    AnimatedAlign,
    AnimatedCrossFade,
)


# --- 1. Typography & Display --------------------------------------------------

class Text(Widget):
    """
    A run of text with styled font, weight, color, alignment and truncation.
    Matches Flutter's native Text widget and Material 3 Typography Scale.

    Parameters:
        value: The text string to display.
        style: Either a Material 3 text theme style name (e.g. 'headlineLarge',
               'titleMedium', 'bodySmall') or a pf.TextStyle instance.
        font_size: Size of the text in logical pixels (e.g. 14, 18.5).
        font_weight: Thickness of the glyphs ('normal', 'bold', 'w600', FontWeight.BOLD).
        color: Hex color string (e.g. '#1877F2', Colors.PRIMARY).
        font_style: 'normal' or 'italic'.
        letter_spacing: Spacing between characters.
        text_align: 'left', 'center', 'right', 'justify'.
        max_lines: Maximum number of lines for the text to span.
        overflow: Truncation behavior ('ellipsis', 'clip', 'fade').
        soft_wrap: Whether the text should break at soft line breaks.
        raw_props: Escape hatch dictionary for unmapped Flutter properties.
    """
    widget_type = "Text"

    def __init__(
        self,
        value: Any = "",
        *,
        key: Optional[str] = None,
        style: Optional[str | TextStyle] = None,
        font_size: Optional[int | float] = None,
        font_weight: Optional[str] = None,
        color: Optional[str] = None,
        font_style: Optional[str] = None,
        letter_spacing: Optional[float] = None,
        text_align: Optional[str] = None,
        max_lines: Optional[int] = None,
        overflow: Optional[str] = None,
        soft_wrap: Optional[bool] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        actual_val = value.value if hasattr(value, "value") else value
        props: dict[str, Any] = {
            "value": str(actual_val),
            "text": str(actual_val),
        }
        if key is not None:
            props["key"] = key
        if style is not None:
            if isinstance(style, str):
                props["style"] = style
                props["theme_style"] = style
            elif isinstance(style, TextStyle):
                props.update(style.to_props())

        if font_size is not None:
            props["font_size"] = font_size
        if font_weight is not None:
            props["font_weight"] = font_weight
        if color is not None:
            props["color"] = color
        if font_style is not None:
            props["font_style"] = font_style
        if letter_spacing is not None:
            props["letter_spacing"] = letter_spacing
        if text_align is not None:
            props["text_align"] = text_align
        if max_lines is not None:
            props["max_lines"] = max_lines
        if overflow is not None:
            props["overflow"] = overflow
        if soft_wrap is not None:
            props["soft_wrap"] = soft_wrap

        super().__init__(raw_props=raw_props, **props)

    def text(self) -> str:
        """Returns the current displayed text (Qt QLabel.text())."""
        return self.props.get("value", "")

    def setText(self, value: Any, *, auto_update: bool = True) -> Text:
        """Dynamically updates the text content (Qt QLabel.setText())."""
        return super().set_text(value, auto_update=auto_update)

    set_text = setText


class Image(Widget):
    """
    Displays an image from a network URL or local source.

    Parameters:
        url: Image source URL (e.g. 'https://...').
        width: Optional width in logical pixels.
        height: Optional height in logical pixels.
        fit: How the image fits its box ('cover', 'contain', 'fill').
        border_radius: Optional rounded corner radius in pixels.
        on_click: Callback invoked when the image is tapped.
    """
    widget_type = "Image"

    def __init__(self, url: str, *,
                 width: Optional[int | float] = None,
                 height: Optional[int | float] = None,
                 fit: Optional[str] = "cover",
                 border_radius: Optional[int | float] = None,
                 on_click: Optional[Callable] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            url=url,
            width=width,
            height=height,
            fit=fit,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        if on_click is not None:
            self.callback_id = _register_callback(on_click)


class Icon(Widget):
    """
    Displays a Material Design vector icon.

    Parameters:
        name: Material icon identifier ('thumb_up', 'favorite', 'comment', 'share', 'person', 'more_horiz', etc.).
        size: Icon size in logical pixels (default: 24.0).
        color: Hex color string (e.g. '#65676B', '#1877F2').
        on_click: Callback invoked when the icon is tapped.
    """
    widget_type = "Icon"

    def __init__(self, name: str, *,
                 size: Optional[int | float] = None,
                 color: Optional[str] = None,
                 on_click: Optional[Callable] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            name=name,
            size=size,
            color=color,
            raw_props=raw_props,
        )
        if on_click is not None:
            self.callback_id = _register_callback(on_click)


class IconButton(Widget):
    """
    A convenient clickable icon button with ripple effect.
    """
    widget_type = "IconButton"

    def __init__(self, name: str, *,
                 on_click: Optional[Callable] = None,
                 on_pressed: Optional[Callable] = None,
                 size: Optional[int | float] = None,
                 color: Optional[str] = None,
                 padding: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            name=name,
            icon=name,
            size=size,
            color=color,
            padding=padding,
            raw_props=raw_props,
        )
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the icon button is tapped (Qt QPushButton.clicked)."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal

    def setIcon(self, name: str) -> IconButton:
        """Sets the icon name (Qt QAbstractButton.setIcon)."""
        self.props["name"] = name
        self.props["icon"] = name
        return self

    set_icon = setIcon

    def icon(self) -> str:
        """Returns the current icon name."""
        return self.props.get("name", "")


# --- 2. Layout & Containers ---------------------------------------------------

class Column(Widget):
    """
    A widget that displays its children in a vertical array.

    Parameters:
        children: List of child widgets to arrange vertically.
        main_axis_alignment: How children align along the vertical axis ('start', 'center', 'space_between').
        cross_axis_alignment: How children align along the horizontal axis ('start', 'center', 'stretch').
        main_axis_size: How much space should be occupied along the main axis ('max' or 'min', MainAxisSize.MAX).
    """
    widget_type = "Column"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 main_axis_alignment: Optional[str] = None,
                 cross_axis_alignment: Optional[str] = None,
                 main_axis_size: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
            main_axis_size=main_axis_size,
            raw_props=raw_props,
        )
        self.children = list(children) if children else []


class Row(Widget):
    """
    A widget that displays its children in a horizontal array.

    Parameters:
        children: List of child widgets to arrange horizontally.
        main_axis_alignment: How children align horizontally ('start', 'center', 'space_between').
        cross_axis_alignment: How children align vertically ('start', 'center').
        main_axis_size: How much space should be occupied along the main axis ('max' or 'min', MainAxisSize.MAX).
    """
    widget_type = "Row"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 main_axis_alignment: Optional[str] = None,
                 cross_axis_alignment: Optional[str] = None,
                 main_axis_size: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
            main_axis_size=main_axis_size,
            raw_props=raw_props,
        )
        self.children = list(children) if children else []


class Wrap(Widget):
    """
    A widget that displays its children in multiple horizontal or vertical runs.
    Unlike Row or Column, Wrap automatically breaks onto a new line when it runs out of space,
    completely preventing RenderFlex overflow errors!

    Parameters:
        children: List of child widgets.
        spacing: How much space to place between children in a run.
        run_spacing: How much space to place between the runs themselves.
        alignment: How children within a run should be placed ('start', 'center', 'end', 'space_between', 'space_around', 'space_evenly').
    """
    widget_type = "Wrap"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 spacing: Optional[int | float] = 8.0,
                 run_spacing: Optional[int | float] = 8.0,
                 alignment: Optional[str] = WrapAlignment.START,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            spacing=spacing,
            run_spacing=run_spacing,
            alignment=alignment,
            raw_props=raw_props,
        )
        self.children = list(children) if children else []


class Stack(Widget):
    """
    Overlays children on top of each other. Use with `Positioned` to place widgets at exact coordinates.
    """
    widget_type = "Stack"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(raw_props=raw_props)
        self.children = list(children) if children else []


class Positioned(Widget):
    """
    Controls where a child of a `Stack` is positioned.
    """
    widget_type = "Positioned"

    def __init__(self, child: Widget, *,
                 top: Optional[int | float] = None,
                 bottom: Optional[int | float] = None,
                 left: Optional[int | float] = None,
                 right: Optional[int | float] = None,
                 width: Optional[int | float] = None,
                 height: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            width=width,
            height=height,
            raw_props=raw_props,
        )
        self.children = [child]


class Container(Widget):
    """
    A convenience box widget combining painting, sizing, padding, and positioning.
    """
    widget_type = "Container"

    def __init__(self, child: Optional[Widget] = None, *,
                 padding: Optional[int | float] = None,
                 margin: Optional[int | float] = None,
                 alignment: Optional[str] = None,
                 color: Optional[str] = None,
                 background_color: Optional[str] = None,
                 width: Optional[int | float] = None,
                 height: Optional[int | float] = None,
                 border_radius: Optional[int | float] = None,
                 shape: Optional[str] = None,
                 border_color: Optional[str] = None,
                 border_width: Optional[int | float] = None,
                 shadow_color: Optional[str] = None,
                 shadow_blur: Optional[int | float] = None,
                 on_click: Optional[Callable] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        effective_color = color or background_color
        super().__init__(
            padding=padding,
            margin=margin,
            alignment=alignment,
            color=effective_color,
            width=width,
            height=height,
            border_radius=border_radius,
            shape=shape,
            border_color=border_color,
            border_width=border_width,
            shadow_color=shadow_color,
            shadow_blur=shadow_blur,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]
        if on_click is not None:
            self.callback_id = _register_callback(on_click)


class Card(Widget):
    """
    A Material Design card with elevation shadows and rounded corners.
    """
    widget_type = "Card"

    def __init__(self, child: Optional[Widget] = None, *,
                 padding: Optional[int | float] = None,
                 elevation: Optional[int | float] = 1.0,
                 margin: Optional[int | float] = 8.0,
                 border_radius: Optional[int | float] = 12.0,
                 color: Optional[str] = None,
                 shadow_color: Optional[str] = None,
                 surface_tint_color: Optional[str] = None,
                 border_color: Optional[str] = None,
                 border_width: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            padding=padding,
            elevation=elevation,
            margin=margin,
            border_radius=border_radius,
            color=color,
            shadow_color=shadow_color,
            surface_tint_color=surface_tint_color,
            border_color=border_color,
            border_width=border_width,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]


class Padding(Widget):
    """
    A widget that insets its child by the given padding.
    """
    widget_type = "Padding"

    def __init__(self, child: Widget, *,
                 all: Optional[int | float] = None,
                 padding: Optional[int | float] = None,
                 horizontal: Optional[int | float] = None,
                 vertical: Optional[int | float] = None,
                 top: Optional[int | float] = None,
                 bottom: Optional[int | float] = None,
                 left: Optional[int | float] = None,
                 right: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        all_val = all if all is not None else padding
        super().__init__(
            all=all_val,
            horizontal=horizontal,
            vertical=vertical,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            raw_props=raw_props,
        )
        self.children = [child]


class SizedBox(Widget):
    """
    A box with a specified fixed width and/or height.
    """
    widget_type = "SizedBox"

    def __init__(self, child: Optional[Widget] = None, *,
                 width: Optional[int | float] = None,
                 height: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            width=width,
            height=height,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]


class Center(Widget):
    """
    Centers its child within itself.
    """
    widget_type = "Center"

    def __init__(self, child: Widget, *,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(raw_props=raw_props)
        self.children = [child]


class Expanded(Widget):
    """
    Expands a child of a Row or Column to fill available space.
    """
    widget_type = "Expanded"

    def __init__(self, child: Widget, *,
                 flex: int = 1,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(flex=flex, raw_props=raw_props)
        self.children = [child]


class Flexible(Widget):
    """
    Controls how a child of a Row, Column, or Flex flexes.
    Unlike Expanded, Flexible does not require the child to fill the available space.
    """
    widget_type = "Flexible"

    def __init__(self, child: Widget, *,
                 flex: int = 1,
                 fit: str = FlexFit.LOOSE,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(flex=flex, fit=fit, raw_props=raw_props)
        self.children = [child]


class FittedBox(Widget):
    """
    Scales and positions its child within itself according to fit.
    Useful for ensuring long text or cards fit without overflowing ('scale_down', 'contain', 'cover').
    """
    widget_type = "FittedBox"

    def __init__(self, child: Widget, *,
                 fit: str = BoxFit.SCALE_DOWN,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(fit=fit, raw_props=raw_props)
        self.children = [child]


class Spacer(Widget):
    """
    Takes up space proportional to flex in a Row or Column.
    """
    widget_type = "Spacer"

    def __init__(self, *, flex: int = 1,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(flex=flex, raw_props=raw_props)


class Divider(Widget):
    """
    A thin horizontal line with padding on either side.
    """
    widget_type = "Divider"

    def __init__(self, *,
                 height: Optional[int | float] = 16.0,
                 thickness: Optional[int | float] = 1.0,
                 indent: Optional[int | float] = None,
                 end_indent: Optional[int | float] = None,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            height=height,
            thickness=thickness,
            indent=indent,
            end_indent=end_indent,
            color=color,
            raw_props=raw_props,
        )


class VerticalDivider(Widget):
    """
    A thin vertical line with padding on either side.
    """
    widget_type = "VerticalDivider"

    def __init__(self, *,
                 width: Optional[int | float] = 16.0,
                 thickness: Optional[int | float] = 1.0,
                 indent: Optional[int | float] = None,
                 end_indent: Optional[int | float] = None,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            width=width,
            thickness=thickness,
            indent=indent,
            end_indent=end_indent,
            color=color,
            raw_props=raw_props,
        )


# --- 3. Scrollable Views ------------------------------------------------------

class ListView(Widget):
    """
    A scrollable list of widgets arranged linearly.
    """
    widget_type = "ListView"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 padding: Optional[int | float] = None,
                 scroll_direction: str = Axis.VERTICAL,
                 shrink_wrap: bool = False,
                 reverse: bool = False,
                 physics: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            padding=padding,
            scroll_direction=scroll_direction,
            shrink_wrap=shrink_wrap,
            reverse=reverse,
            physics=physics,
            raw_props=raw_props,
        )
        self.children = list(children) if children else []


class SingleChildScrollView(Widget):
    """
    A box in which a single widget can be scrolled.

    Parameters:
        child: The single widget to scroll.
        scroll_direction: Direction of scroll ('vertical' or 'horizontal'). Default is 'vertical'.
        reverse: Whether the scroll view scrolls in the reading direction. Default is False.
        physics: How the scroll view should respond to user input ('bouncing', 'clamping', 'never', 'always').
        padding: Padding inside the scroll view.
    """
    widget_type = "SingleChildScrollView"

    def __init__(self, child: Widget, *,
                 scroll_direction: str = Axis.VERTICAL,
                 reverse: bool = False,
                 physics: Optional[str] = None,
                 padding: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            scroll_direction=scroll_direction,
            reverse=reverse,
            physics=physics,
            padding=padding,
            raw_props=raw_props,
        )
        self.children = [child]


class ListTile(Widget):
    """
    A single fixed-height row that typically contains some text as well as a leading or trailing icon.

    Parameters:
        title: Primary content of the list tile (string or Widget).
        subtitle: Additional content displayed below the title (string or Widget).
        leading: A widget to display before the title (e.g. Icon, Image).
        trailing: A widget to display after the title (e.g. Icon, Switch, Checkbox).
        is_three_line: Whether this list tile is intended to display three lines of text.
        dense: Whether this list tile is part of a vertically dense list.
        enabled: Whether this list tile is interactive.
        selected: If this tile is also [enabled] then icons and text are rendered with the selected color.
        tile_color: Background color of the tile when not selected.
        selected_tile_color: Background color of the tile when selected.
        on_click: Callback invoked when the tile is tapped.
        on_tap: Alias for on_click.
    """
    widget_type = "ListTile"

    def __init__(
        self,
        title: Optional[Widget | str] = None,
        *,
        subtitle: Optional[Widget | str] = None,
        leading: Optional[Widget] = None,
        trailing: Optional[Widget] = None,
        is_three_line: bool = False,
        dense: bool = False,
        enabled: bool = True,
        selected: bool = False,
        tile_color: Optional[str] = None,
        selected_tile_color: Optional[str] = None,
        on_click: Optional[Callable] = None,
        on_tap: Optional[Callable] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        props: dict[str, Any] = {
            "is_three_line": is_three_line,
            "dense": dense,
            "enabled": enabled,
            "selected": selected,
        }
        if tile_color:
            props["tile_color"] = tile_color
        if selected_tile_color:
            props["selected_tile_color"] = selected_tile_color
        if isinstance(title, str):
            props["title"] = title
        if isinstance(subtitle, str):
            props["subtitle"] = subtitle

        super().__init__(raw_props=raw_props, **props)

        if isinstance(title, Widget):
            title.props["slot"] = "title"
            self.children.append(title)
        if isinstance(subtitle, Widget):
            subtitle.props["slot"] = "subtitle"
            self.children.append(subtitle)
        if leading is not None:
            leading.props["slot"] = "leading"
            self.children.append(leading)
        if trailing is not None:
            trailing.props["slot"] = "trailing"
            self.children.append(trailing)

        handler = on_tap or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the list tile is tapped."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal



# --- 4. Inputs & Interactive Controls -----------------------------------------

class Button(Widget):
    """
    An elevated Material button with optional icon, label, and click callback.
    """
    widget_type = "Button"

    def __init__(
        self,
        label: Any = "",
        *,
        text: Optional[str] = None,
        key: Optional[str] = None,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        on_pressed: Optional[Callable] = None,
        color: Optional[str] = None,
        background_color: Optional[str] = None,
        border_radius: Optional[float] = None,
        elevation: Optional[float] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        raw = text if (label == "" or label is None) and text is not None else label
        actual_label = raw.value if hasattr(raw, "value") else raw
        super().__init__(
            label=str(actual_label),
            text=str(actual_label),
            key=key,
            icon=icon,
            color=color,
            background_color=background_color,
            border_radius=border_radius,
            elevation=elevation,
            raw_props=raw_props,
            **kwargs,
        )
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the button is clicked (Qt QPushButton.clicked)."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal

    def on_click(self, fn: Callable) -> Button:
        self.clicked.connect(fn)
        return self

    def text(self) -> str:
        """Returns the button label text (Qt QPushButton.text())."""
        return self.props.get("label", "")

    def setText(self, label: Any, *, auto_update: bool = True) -> Button:
        """Sets the button label text (Qt QPushButton.setText())."""
        return super().set_text(label, auto_update=auto_update)

    set_text = setText
    set_label = setText

    def isEnabled(self) -> bool:
        """Returns whether the button is enabled (Qt QWidget.isEnabled())."""
        return self.props.get("enabled") != "false"

    is_enabled = isEnabled

    def setEnabled(self, enabled: bool) -> Button:
        """Sets whether the button is enabled (Qt QWidget.setEnabled())."""
        self.props["enabled"] = "true" if enabled else "false"
        return self

    set_enabled = setEnabled


# Flutter alias for developers coming from Flutter
ElevatedButton = Button


class OutlinedButton(Widget):
    """
    A Material 3 Outlined button with a border stroke and transparent background.
    """
    widget_type = "OutlinedButton"

    def __init__(
        self,
        label: Any = "",
        *,
        text: Optional[str] = None,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        on_pressed: Optional[Callable] = None,
        color: Optional[str] = None,
        border_color: Optional[str] = None,
        border_width: Optional[float] = 1.0,
        border_radius: Optional[float] = 8.0,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        raw = text if (label == "" or label is None) and text is not None else label
        super().__init__(
            label=str(raw),
            text=str(raw),
            icon=icon,
            color=color,
            border_color=border_color,
            border_width=border_width,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the button is clicked (Qt QPushButton.clicked)."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal

    def on_click(self, fn: Callable) -> OutlinedButton:
        self.clicked.connect(fn)
        return self

    def text(self) -> str:
        """Returns the button label text (Qt QPushButton.text())."""
        return self.props.get("label", "")

    def setText(self, label: Any) -> OutlinedButton:
        """Sets the button label text (Qt QPushButton.setText())."""
        self.props["label"] = str(label)
        return self

    set_text = setText
    set_label = setText

    def isEnabled(self) -> bool:
        """Returns whether the button is enabled (Qt QWidget.isEnabled())."""
        return self.props.get("enabled") != "false"

    is_enabled = isEnabled

    def setEnabled(self, enabled: bool) -> OutlinedButton:
        """Sets whether the button is enabled (Qt QWidget.setEnabled())."""
        self.props["enabled"] = "true" if enabled else "false"
        return self

    set_enabled = setEnabled


class TextButton(Widget):
    """
    A Material 3 Text button (flat button without elevation or outline).
    """
    widget_type = "TextButton"

    def __init__(
        self,
        label: Any = "",
        *,
        text: Optional[str] = None,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        on_pressed: Optional[Callable] = None,
        color: Optional[str] = None,
        border_radius: Optional[float] = 8.0,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        raw = text if (label == "" or label is None) and text is not None else label
        super().__init__(
            label=str(raw),
            text=str(raw),
            icon=icon,
            color=color,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the button is clicked (Qt QPushButton.clicked)."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal

    def on_click(self, fn: Callable) -> TextButton:
        self.clicked.connect(fn)
        return self

    def text(self) -> str:
        """Returns the button label text (Qt QPushButton.text())."""
        return self.props.get("label", "")

    def setText(self, label: Any) -> TextButton:
        """Sets the button label text (Qt QPushButton.setText())."""
        self.props["label"] = str(label)
        return self

    set_text = setText
    set_label = setText

    def isEnabled(self) -> bool:
        """Returns whether the button is enabled (Qt QWidget.isEnabled())."""
        return self.props.get("enabled") != "false"

    is_enabled = isEnabled

    def setEnabled(self, enabled: bool) -> TextButton:
        """Sets whether the button is enabled (Qt QWidget.setEnabled())."""
        self.props["enabled"] = "true" if enabled else "false"
        return self

    set_enabled = setEnabled


class FloatingActionButton(Widget):
    """
    A Material Design floating action button.
    A circular icon button that hovers over content to promote a primary action in the application.

    Supports both regular circular FABs and extended FABs with text labels.
    """
    widget_type = "FloatingActionButton"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        icon: Optional[str] = None,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        mini: bool = False,
        elevation: Optional[float] = None,
        background_color: Optional[str] = None,
        foreground_color: Optional[str] = None,
        color: Optional[str] = None,
        on_pressed: Optional[Callable] = None,
        on_click: Optional[Callable] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        eff_foreground = foreground_color or color
        super().__init__(
            icon=icon,
            label=label,
            tooltip=tooltip,
            mini=mini,
            elevation=elevation,
            background_color=background_color,
            foreground_color=eff_foreground,
            color=eff_foreground,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @classmethod
    def extended(
        cls,
        label: str,
        *,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        elevation: Optional[float] = None,
        background_color: Optional[str] = None,
        foreground_color: Optional[str] = None,
        on_pressed: Optional[Callable] = None,
        on_click: Optional[Callable] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ) -> FloatingActionButton:
        """Creates a wider, stadium-shaped FloatingActionButton that includes a text label and optional icon."""
        return cls(
            label=label,
            icon=icon,
            tooltip=tooltip,
            elevation=elevation,
            background_color=background_color,
            foreground_color=foreground_color,
            on_pressed=on_pressed,
            on_click=on_click,
            raw_props=raw_props,
        )

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the floating action button is pressed."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal


class Badge(Widget):
    """
    A Material 3 Badge widget that decorates a child widget with a small status or count badge.
    """
    widget_type = "Badge"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        label: Optional[str] = None,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        is_small: bool = False,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            label=label,
            background_color=background_color,
            text_color=text_color,
            is_small=is_small,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]


class Chip(Widget):
    """
    A compact Material 3 ActionChip/Chip element that represents an input, attribute, or action.
    """
    widget_type = "Chip"

    def __init__(
        self,
        label: str,
        *,
        avatar: Optional[str] = None,
        background_color: Optional[str] = None,
        on_pressed: Optional[Callable] = None,
        on_click: Optional[Callable] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            label=label,
            avatar=avatar,
            background_color=background_color,
            raw_props=raw_props,
        )
        handler = on_pressed or on_click
        if handler is not None:
            self.clicked.connect(handler)

    @property
    def clicked(self) -> QtSignal:
        """Qt signal emitted when the chip is clicked."""
        if not hasattr(self, "_clicked_signal"):
            self._clicked_signal = QtSignal(self, "callback_id")
        return self._clicked_signal


ActionChip = Chip



class TextField(Widget):
    """
    A Material text field for user text input.
    Supports TextEditingController, labels, hints, validation errors,
    password masking, custom borders, icons, and keyboard types.
    """
    widget_type = "TextField"

    def __init__(
        self,
        value: str = "",
        *,
        key: Optional[str] = None,
        controller: Optional[TextEditingController] = None,
        label: Optional[str] = None,
        label_text: Optional[str] = None,
        placeholder: Optional[str] = None,
        hint_text: Optional[str] = None,
        helper_text: Optional[str] = None,
        error_text: Optional[str] = None,
        obscure_text: bool = False,
        keyboard_type: str = "text",
        text_align: str = "left",
        read_only: bool = False,
        enabled: bool = True,
        autofocus: bool = False,
        autocorrect: bool = True,
        cursor_color: Optional[str] = None,
        max_length: Optional[int] = None,
        content_padding: Optional[int | float] = None,
        prefix_text: Optional[str] = None,
        suffix_text: Optional[str] = None,
        text_capitalization: Optional[str] = None,
        max_lines: Optional[int] = 1,
        min_lines: Optional[int] = 1,
        prefix_icon: Optional[str] = None,
        suffix_icon: Optional[str] = None,
        on_suffix_icon_click: Optional[Callable[[], None]] = None,
        border: Any = "outline",
        border_radius: Optional[float] = None,
        border_color: Optional[str] = None,
        focused_border_color: Optional[str] = None,
        filled: bool = False,
        fill_color: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        on_changed: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        on_submitted: Optional[Callable[[str], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        self.controller = controller
        initial_val = controller.text if controller is not None else str(value)

        # Parse border if passed as OutlineInputBorder or UnderlineInputBorder
        border_str = "outline"
        b_radius = border_radius
        b_color = border_color
        if isinstance(border, str):
            border_str = border
        elif hasattr(border, "type"):
            border_str = border.type
            if hasattr(border, "border_radius"):
                b_radius = border.border_radius
            if hasattr(border, "border_color"):
                b_color = border.border_color

        super().__init__(
            key=key,
            value=initial_val,
            label=label or label_text,
            hint=hint_text or placeholder,
            placeholder=hint_text or placeholder,
            helper_text=helper_text,
            error_text=error_text,
            obscure_text=obscure_text,
            keyboard_type=keyboard_type,
            text_align=text_align,
            read_only=read_only,
            enabled=enabled,
            autofocus=autofocus,
            autocorrect=autocorrect,
            cursor_color=cursor_color,
            max_length=max_length,
            content_padding=content_padding,
            prefix_text=prefix_text,
            suffix_text=suffix_text,
            text_capitalization=text_capitalization,
            max_lines=max_lines,
            min_lines=min_lines,
            prefix_icon=prefix_icon,
            suffix_icon=suffix_icon,
            border=border_str,
            border_radius=b_radius,
            border_color=b_color,
            focused_border_color=focused_border_color,
            filled=filled,
            fill_color=fill_color,
            raw_props=raw_props,
        )

        # Setup Qt-style textChanged signal
        self._text_changed_signal = QtSignal(self, "callback_id")
        def _sync_internal(val: str = "") -> None:
            self.props["value"] = str(val)
            if self.controller is not None:
                self.controller.text = str(val)
        self._text_changed_signal.connect(_sync_internal)

        change_handler = on_changed or on_change
        if change_handler is not None:
            self._text_changed_signal.connect(change_handler)

        if self.controller is not None:
            self.controller.add_listener(self._sync_from_controller)

        if on_suffix_icon_click is not None:
            self.props["suffix_callback_id"] = _register_callback(on_suffix_icon_click)

        # Setup Qt-style returnPressed signal
        self._return_pressed_signal = QtSignal(self, "submit_callback_id")
        submit_handler = on_submitted or on_submit
        if submit_handler is not None:
            self._return_pressed_signal.connect(submit_handler)

    def _sync_from_controller(self) -> None:
        if self.controller is not None:
            self.props["value"] = self.controller.text

    @property
    def textChanged(self) -> QtSignal:
        """Qt signal emitted whenever the text changes (Qt QLineEdit.textChanged)."""
        return self._text_changed_signal

    text_changed = textChanged

    @property
    def returnPressed(self) -> QtSignal:
        """Qt signal emitted when the user presses Enter/Submit (Qt QLineEdit.returnPressed)."""
        return self._return_pressed_signal

    return_pressed = returnPressed

    @property
    def value(self) -> str:
        if self.controller is not None:
            return self.controller.text
        return self.props.get("value", "")

    def set_value(self, value: str, *, auto_update: bool = True) -> TextField:
        self.props["value"] = str(value)
        if self.controller is not None:
            self.controller.text = str(value)
        if auto_update:
            self._notify_dirty()
        return self

    def text(self) -> str:
        """Returns the current text in the field (Qt QLineEdit.text())."""
        return self.value

    def setText(self, value: str, *, auto_update: bool = True) -> TextField:
        """Sets the text in the field (Qt QLineEdit.setText())."""
        return self.set_value(value, auto_update=auto_update)

    set_text = setText

    def clear(self, *, auto_update: bool = True) -> TextField:
        """Clears the text in the field (Qt QLineEdit.clear())."""
        return self.set_value("", auto_update=auto_update)

    def setPlaceholderText(self, text: str) -> TextField:
        """Sets the placeholder/hint text (Qt QLineEdit.setPlaceholderText())."""
        self.props["placeholder"] = str(text)
        self.props["hint"] = str(text)
        return self

    set_placeholder_text = setPlaceholderText
    set_placeholder = setPlaceholderText

    def setReadOnly(self, ro: bool) -> TextField:
        """Sets whether the field is read-only (Qt QLineEdit.setReadOnly())."""
        self.props["read_only"] = "true" if ro else "false"
        return self

    set_read_only = setReadOnly

    def isReadOnly(self) -> bool:
        """Returns whether the field is read-only (Qt QLineEdit.isReadOnly())."""
        return self.props.get("read_only") == "true"

    is_read_only = isReadOnly

    def setEnabled(self, enabled: bool) -> TextField:
        """Sets whether the field is enabled (Qt QWidget.setEnabled())."""
        self.props["enabled"] = "true" if enabled else "false"
        return self

    set_enabled = setEnabled

    def isEnabled(self) -> bool:
        """Returns whether the field is enabled (Qt QWidget.isEnabled())."""
        return self.props.get("enabled") != "false"

    is_enabled = isEnabled


class TextFormField(TextField):
    """
    A FormField that wraps a TextField, providing integration with Form and FormKey,
    validation logic (via Validators), error display, and on_saved hooks.
    """
    widget_type = "TextField"

    def __init__(
        self,
        value: str = "",
        *,
        name: Optional[str] = None,
        controller: Optional[TextEditingController] = None,
        validator: Optional[Callable[[str], Optional[str]]] = None,
        on_saved: Optional[Callable[[str], None]] = None,
        form_key: Optional[FormKey] = None,
        initial_value: Optional[str] = None,
        label: Optional[str] = None,
        label_text: Optional[str] = None,
        placeholder: Optional[str] = None,
        hint_text: Optional[str] = None,
        helper_text: Optional[str] = None,
        error_text: Optional[str] = None,
        obscure_text: bool = False,
        keyboard_type: str = "text",
        text_align: str = "left",
        read_only: bool = False,
        enabled: bool = True,
        autofocus: bool = False,
        autocorrect: bool = True,
        cursor_color: Optional[str] = None,
        max_length: Optional[int] = None,
        content_padding: Optional[int | float] = None,
        prefix_text: Optional[str] = None,
        suffix_text: Optional[str] = None,
        text_capitalization: Optional[str] = None,
        max_lines: Optional[int] = 1,
        min_lines: Optional[int] = 1,
        prefix_icon: Optional[str] = None,
        suffix_icon: Optional[str] = None,
        on_suffix_icon_click: Optional[Callable[[], None]] = None,
        border: Any = "outline",
        border_radius: Optional[float] = None,
        border_color: Optional[str] = None,
        focused_border_color: Optional[str] = None,
        filled: bool = False,
        fill_color: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        on_changed: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        on_submitted: Optional[Callable[[str], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        actual_val = initial_value if initial_value is not None else value
        super().__init__(
            value=actual_val,
            controller=controller,
            label=label,
            label_text=label_text,
            placeholder=placeholder,
            hint_text=hint_text,
            helper_text=helper_text,
            error_text=error_text,
            obscure_text=obscure_text,
            keyboard_type=keyboard_type,
            text_align=text_align,
            read_only=read_only,
            enabled=enabled,
            autofocus=autofocus,
            autocorrect=autocorrect,
            cursor_color=cursor_color,
            max_length=max_length,
            content_padding=content_padding,
            prefix_text=prefix_text,
            suffix_text=suffix_text,
            text_capitalization=text_capitalization,
            max_lines=max_lines,
            min_lines=min_lines,
            prefix_icon=prefix_icon,
            suffix_icon=suffix_icon,
            on_suffix_icon_click=on_suffix_icon_click,
            border=border,
            border_radius=border_radius,
            border_color=border_color,
            focused_border_color=focused_border_color,
            filled=filled,
            fill_color=fill_color,
            on_change=on_change,
            on_changed=on_changed,
            on_submit=on_submit,
            on_submitted=on_submitted,
            raw_props=raw_props,
        )
        self.name = name
        self.validator = validator
        self.on_saved = on_saved
        self._initial_value = actual_val
        self.form_key = form_key
        if form_key:
            form_key.register(self)

    def _register_with_form_key(self, form_key: FormKey) -> None:
        self.form_key = form_key
        form_key.register(self)

    def validate_field(self) -> bool:
        """Runs the validator function on this field's current value."""
        if not self.validator:
            self.props.pop("error_text", None)
            return True
        err = self.validator(self.value)
        if err:
            self.props["error_text"] = str(err)
            return False
        else:
            self.props.pop("error_text", None)
            return True

    def reset_field(self) -> None:
        """Resets the field to its initial value and clears errors."""
        self.set_value(self._initial_value)
        self.props.pop("error_text", None)

    def save_field(self) -> None:
        """Invokes on_saved if defined."""
        if self.on_saved:
            self.on_saved(self.value)


class DropdownMenuItem(Widget):
    """
    An item in a DropdownButton menu or DropdownMenu entries.
    """
    widget_type = "DropdownMenuItem"

    def __init__(
        self,
        value: Any,
        child: Optional[Widget] = None,
        *,
        label: Optional[str] = None,
        disabled: bool = False,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            value=str(value),
            label=label or (str(value) if child is None else None),
            disabled=disabled,
            raw_props=raw_props,
        )
        if child is not None:
            self.children = [child]


class DropdownButton(Widget):
    """
    A Material Design dropdown button.
    
    Parameters:
        items: List of DropdownMenuItem instances or strings.
        value: Currently selected value.
        hint: Text or Widget shown when no value is selected.
        on_change: Callback invoked when the user selects an item: fn(new_value).
        on_changed: Alias for on_change.
        is_expanded: Whether the dropdown stretches to fill its parent horizontally (default True).
        icon: Icon name to display for the dropdown arrow (default 'arrow_drop_down').
        elevation: Elevation of the dropdown popup menu (default 8).
    """
    widget_type = "DropdownButton"

    def __init__(
        self,
        items: Sequence[DropdownMenuItem | str | Any],
        *,
        value: Optional[Any] = None,
        hint: Optional[str | Widget] = None,
        on_change: Optional[Callable[[str], None]] = None,
        on_changed: Optional[Callable[[str], None]] = None,
        is_expanded: bool = True,
        icon: Optional[str] = "arrow_drop_down",
        icon_size: float = 24.0,
        elevation: int = 8,
        border_radius: Optional[float] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        hint_text = hint if isinstance(hint, str) else None
        super().__init__(
            value=str(value) if value is not None else None,
            hint=hint_text,
            is_expanded=is_expanded,
            icon=icon,
            icon_size=icon_size,
            elevation=elevation,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        if hint is not None and not isinstance(hint, str):
            hint.props["slot"] = "hint"
            self.children.append(hint)

        converted_items: list[Widget] = []
        for item in items:
            if isinstance(item, DropdownMenuItem):
                converted_items.append(item)
            else:
                converted_items.append(DropdownMenuItem(value=item, label=str(item)))
        self.children.extend(converted_items)

        # Setup Qt-style currentTextChanged signal
        self._current_text_changed_signal = QtSignal(self, "callback_id")
        def _sync_val(val: str = "") -> None:
            self.props["value"] = str(val)
        self._current_text_changed_signal.connect(_sync_val)

        handler = on_changed or on_change
        if handler:
            self._current_text_changed_signal.connect(handler)

    @property
    def currentTextChanged(self) -> QtSignal:
        """Qt signal emitted when the selected item changes (Qt QComboBox.currentTextChanged)."""
        return self._current_text_changed_signal

    current_text_changed = currentTextChanged
    currentIndexChanged = currentTextChanged
    current_index_changed = currentTextChanged

    @property
    def value(self) -> Optional[str]:
        return self.props.get("value")

    def set_value(self, value: Any) -> DropdownButton:
        self.props["value"] = str(value)
        return self

    def currentText(self) -> Optional[str]:
        """Returns currently selected text (Qt QComboBox.currentText())."""
        return self.value

    current_text = currentText

    def setCurrentText(self, text: Any) -> DropdownButton:
        """Sets currently selected text (Qt QComboBox.setCurrentText())."""
        return self.set_value(text)

    set_current_text = setCurrentText


class DropdownMenu(Widget):
    """
    A Material 3 DropdownMenu widget with text field selection and dropdown list.
    """
    widget_type = "DropdownMenu"

    def __init__(
        self,
        entries: Sequence[DropdownMenuItem | str | Any],
        *,
        initial_selection: Optional[Any] = None,
        label: Optional[str] = None,
        hint_text: Optional[str] = None,
        leading_icon: Optional[str] = None,
        trailing_icon: Optional[str] = None,
        width: Optional[float] = None,
        on_selected: Optional[Callable[[str], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            initial_selection=str(initial_selection) if initial_selection is not None else None,
            label=label,
            hint_text=hint_text,
            leading_icon=leading_icon,
            trailing_icon=trailing_icon,
            width=width,
            raw_props=raw_props,
        )
        converted: list[Widget] = []
        for e in entries:
            if isinstance(e, DropdownMenuItem):
                converted.append(e)
            else:
                converted.append(DropdownMenuItem(value=e, label=str(e)))
        self.children.extend(converted)

        if on_selected:
            self.callback_id = _register_callback(on_selected)


class Switch(Widget):
    """
    A Material boolean toggle switch.
    """
    widget_type = "Switch"

    def __init__(self, value: bool = False, *,
                 on_change: Optional[Callable[[bool], None]] = None,
                 active_color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            value=value,
            active_color=active_color,
            raw_props=raw_props,
        )
        if on_change is not None:
            self.toggled.connect(on_change)

    @property
    def toggled(self) -> QtSignal:
        """Qt signal emitted when the switch is toggled (Qt QAbstractButton.toggled)."""
        if not hasattr(self, "_toggled_signal"):
            def _to_bool(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                return str(v).lower() in ("true", "1")
            self._toggled_signal = QtSignal(self, "callback_id", value_converter=_to_bool)
            def _sync_val(v: bool):
                self.props["value"] = "true" if v else "false"
            self._toggled_signal.connect(_sync_val)
        return self._toggled_signal

    stateChanged = toggled
    state_changed = toggled

    def isChecked(self) -> bool:
        """Returns whether the switch is currently ON (Qt QAbstractButton.isChecked())."""
        return self.props.get("value") == "true"

    is_checked = isChecked

    def setChecked(self, checked: bool, *, auto_update: bool = True) -> Switch:
        """Sets whether the switch is ON (Qt QAbstractButton.setChecked())."""
        self.props["value"] = "true" if checked else "false"
        if auto_update:
            self._notify_dirty()
        return self

    set_checked = setChecked

    def toggle(self) -> Switch:
        """Inverts the current switch state (Qt QAbstractButton.toggle())."""
        return self.setChecked(not self.isChecked())


class Checkbox(Widget):
    """
    A Material checkbox control.
    """
    widget_type = "Checkbox"

    def __init__(self, value: bool = False, *,
                 on_change: Optional[Callable[[bool], None]] = None,
                 active_color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            value=value,
            active_color=active_color,
            raw_props=raw_props,
        )
        if on_change is not None:
            self.toggled.connect(on_change)

    @property
    def toggled(self) -> QtSignal:
        """Qt signal emitted when the checkbox is toggled (Qt QCheckBox.toggled)."""
        if not hasattr(self, "_toggled_signal"):
            def _to_bool(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                return str(v).lower() in ("true", "1")
            self._toggled_signal = QtSignal(self, "callback_id", value_converter=_to_bool)
            def _sync_val(v: bool):
                self.props["value"] = "true" if v else "false"
            self._toggled_signal.connect(_sync_val)
        return self._toggled_signal

    stateChanged = toggled
    state_changed = toggled

    def isChecked(self) -> bool:
        """Returns whether the checkbox is checked (Qt QCheckBox.isChecked())."""
        return self.props.get("value") == "true"

    is_checked = isChecked

    def setChecked(self, checked: bool, *, auto_update: bool = True) -> Checkbox:
        """Sets whether the checkbox is checked (Qt QCheckBox.setChecked())."""
        self.props["value"] = "true" if checked else "false"
        if auto_update:
            self._notify_dirty()
        return self

    set_checked = setChecked

    def toggle(self) -> Checkbox:
        """Inverts the current checkbox state (Qt QCheckBox.toggle())."""
        return self.setChecked(not self.isChecked())


class Slider(Widget):
    """
    A Material Design slider for selecting a numeric value from a range of values.
    Supports min, max, divisions, labels, custom colors, and event callbacks.

    Parameters:
        value: The currently selected value (between min and max).
        min: The minimum value the user can select. Default is 0.0.
        max: The maximum value the user can select. Default is 1.0.
        divisions: The number of discrete divisions. If None, the slider is continuous.
        label: A label to display above the slider thumb when active.
        active_color: Color of the slider track and thumb for selected portion.
        inactive_color: Color of the slider track for unselected portion.
        on_change: Callback invoked when the user drags the slider: fn(float).
        on_changed: Alias for on_change.
    """
    widget_type = "Slider"

    def __init__(
        self,
        value: float = 0.0,
        *,
        min: float = 0.0,
        max: float = 1.0,
        divisions: Optional[int] = None,
        label: Optional[str] = None,
        active_color: Optional[str] = None,
        inactive_color: Optional[str] = None,
        on_change: Optional[Callable[[float], None]] = None,
        on_changed: Optional[Callable[[float], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            value=value,
            min=min,
            max=max,
            divisions=divisions,
            label=label,
            active_color=active_color,
            inactive_color=inactive_color,
            raw_props=raw_props,
        )
        handler = on_changed or on_change
        if handler is not None:
            self.valueChanged.connect(handler)

    @property
    def valueChanged(self) -> QtSignal:
        """Qt signal emitted when the slider position changes (Qt QSlider.valueChanged)."""
        if not hasattr(self, "_value_changed_signal"):
            def _to_float(v: Any) -> float:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return 0.0
            self._value_changed_signal = QtSignal(self, "callback_id", value_converter=_to_float)
            def _sync_val(v: float):
                self.props["value"] = str(v)
            self._value_changed_signal.connect(_sync_val)
        return self._value_changed_signal

    value_changed = valueChanged

    def value(self) -> float:
        """Returns the current slider numeric value."""
        try:
            return float(self.props.get("value", 0.0))
        except (TypeError, ValueError):
            return 0.0

    def setValue(self, val: float, *, auto_update: bool = True) -> Slider:
        """Sets the slider numeric value."""
        self.props["value"] = str(val)
        if auto_update:
            self._notify_dirty()
        return self

    set_value = setValue


class CircularProgressIndicator(Widget):
    """
    A circular progress indicator showing activity.
    """
    widget_type = "CircularProgressIndicator"

    def __init__(self, *,
                 stroke_width: Optional[int | float] = 4.0,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            stroke_width=stroke_width,
            color=color,
            raw_props=raw_props,
        )


# --- 6. Navigation, Layout & Scaffolding ---------------------------------------

class SafeArea(Widget):
    """
    A widget that insets its child with sufficient padding to avoid intrusions
    by the operating system (e.g. status bar, camera notch, navigation buttons).
    """
    widget_type = "SafeArea"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        top: bool = True,
        bottom: bool = True,
        left: bool = True,
        right: bool = True,
        minimum: float = 0.0,
        maintain_bottom_view_padding: bool = False,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            minimum=minimum,
            maintain_bottom_view_padding=maintain_bottom_view_padding,
            raw_props=raw_props,
        )
        if child is not None:
            self.children.append(child)


class AppBar(Widget):
    """
    A Material Design app bar that typically appears at the top of a Scaffold.
    """
    widget_type = "AppBar"

    def __init__(
        self,
        title: Optional[str | Widget] = None,
        *,
        leading: Optional[Widget] = None,
        actions: Optional[Sequence[Widget]] = None,
        bottom: Optional[Widget] = None,
        background_color: Optional[str] = None,
        elevation: Optional[float] = None,
        scrolled_under_elevation: Optional[float] = None,
        shadow_color: Optional[str] = None,
        surface_tint_color: Optional[str] = None,
        toolbar_height: Optional[float] = None,
        title_spacing: Optional[float] = None,
        center_title: Optional[bool] = None,
        automatically_imply_leading: bool = True,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            title=title if isinstance(title, str) else None,
            background_color=background_color,
            elevation=elevation,
            scrolled_under_elevation=scrolled_under_elevation,
            shadow_color=shadow_color,
            surface_tint_color=surface_tint_color,
            toolbar_height=toolbar_height,
            title_spacing=title_spacing,
            center_title=center_title,
            raw_props=raw_props,
        )
        if isinstance(title, Widget):
            title.props["slot"] = "title"
            self.children.append(title)

        # Automatic back button synthesis if on a pushed page
        if leading is None and automatically_imply_leading:
            from pyflutter.core.navigation import Navigator
            if Navigator.can_pop():
                from pyflutter.core.constants import Icons
                leading = IconButton(
                    name=Icons.ARROW_BACK,
                    on_pressed=Navigator.pop,
                )

        if leading is not None:
            leading.props["slot"] = "leading"
            self.children.append(leading)
        if actions is not None:
            for act in actions:
                act.props["slot"] = "action"
                self.children.append(act)
        if bottom is not None:
            bottom.props["slot"] = "bottom"
            self.children.append(bottom)


class Scaffold(Widget):
    """
    Implements the basic Material Design visual layout structure.
    Provides slots for an AppBar, body, floating action button, and bottom navigation.
    """
    widget_type = "Scaffold"

    def __init__(
        self,
        body: Optional[Widget] = None,
        *,
        app_bar: Optional[AppBar | Widget] = None,
        bottom_navigation_bar: Optional[Widget] = None,
        floating_action_button: Optional[Widget] = None,
        floating_action_button_location: Optional[str] = None,
        drawer: Optional[Widget] = None,
        end_drawer: Optional[Widget] = None,
        bottom_sheet: Optional[Widget] = None,
        background_color: Optional[str] = None,
        resize_to_avoid_bottom_inset: bool = True,
        extend_body: bool = False,
        extend_body_behind_app_bar: bool = False,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            background_color=background_color,
            floating_action_button_location=floating_action_button_location,
            resize_to_avoid_bottom_inset=resize_to_avoid_bottom_inset,
            extend_body=extend_body,
            extend_body_behind_app_bar=extend_body_behind_app_bar,
            raw_props=raw_props,
        )
        if app_bar is not None:
            app_bar.props["slot"] = "app_bar"
            self.children.append(app_bar)
        if body is not None:
            body.props["slot"] = "body"
            self.children.append(body)
        if bottom_navigation_bar is not None:
            bottom_navigation_bar.props["slot"] = "bottom_bar"
            self.children.append(bottom_navigation_bar)
        if floating_action_button is not None:
            floating_action_button.props["slot"] = "fab"
            self.children.append(floating_action_button)
        if drawer is not None:
            drawer.props["slot"] = "drawer"
            self.children.append(drawer)
        if end_drawer is not None:
            end_drawer.props["slot"] = "end_drawer"
            self.children.append(end_drawer)
        if bottom_sheet is not None:
            bottom_sheet.props["slot"] = "bottom_sheet"
            self.children.append(bottom_sheet)


class BottomNavigationBarItem(Widget):
    """
    An item in a BottomNavigationBar with an icon and label.
    """
    widget_type = "BottomNavigationBarItem"

    def __init__(self, icon: str, label: str, *, raw_props: Optional[dict[str, Any]] = None):
        super().__init__(icon=icon, label=label, raw_props=raw_props)


class BottomNavigationBar(Widget):
    """
    A Material widget displayed at the bottom of an app for selecting among a small
    number of views, typically between three and five.
    """
    widget_type = "BottomNavigationBar"

    def __init__(
        self,
        items: Sequence[BottomNavigationBarItem],
        *,
        current_index: int = 0,
        on_tap: Optional[Callable[[int], None]] = None,
        background_color: Optional[str] = None,
        selected_color: Optional[str] = None,
        unselected_color: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            current_index=current_index,
            background_color=background_color,
            selected_color=selected_color,
            unselected_color=unselected_color,
            raw_props=raw_props,
        )
        self.children.extend(items)
        if on_tap is not None:
            def handler(index: str = "0", **_):
                try:
                    on_tap(int(index))
                except Exception:
                    pass
            self.callback_id = _register_callback(handler)


class PageView(Widget):
    """
    A scrollable list of pages that works page by page.
    """
    widget_type = "PageView"

    def __init__(
        self,
        children: Sequence[Widget],
        *,
        scroll_direction: str = "horizontal",
        on_page_changed: Optional[Callable[[int], None]] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            scroll_direction=scroll_direction,
            raw_props=raw_props,
        )
        self.children.extend(children)
        if on_page_changed is not None:
            def handler(page: str = "0", **_):
                try:
                    on_page_changed(int(page))
                except Exception:
                    pass
            self.callback_id = _register_callback(handler)


class Tab(Widget):
    """
    A Material Design [TabBar] tab.
    """
    widget_type = "Tab"

    def __init__(self, text: Optional[str] = None, *, icon: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(text=text, icon=icon, raw_props=raw_props)


class TabBar(Widget):
    """
    A Material Design widget that displays a horizontal row of tabs.
    """
    widget_type = "TabBar"

    def __init__(
        self,
        tabs: Sequence[Tab],
        *,
        indicator_color: Optional[str] = None,
        label_color: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            indicator_color=indicator_color,
            label_color=label_color,
            raw_props=raw_props,
        )
        self.children.extend(tabs)


class TabBarView(Widget):
    """
    A page view that displays the widget corresponding to the currently selected tab.
    """
    widget_type = "TabBarView"

    def __init__(self, children: Sequence[Widget], *, raw_props: Optional[dict[str, Any]] = None):
        super().__init__(raw_props=raw_props)
        self.children.extend(children)


class DefaultTabController(Widget):
    """
    The [DefaultTabController] is used to share a [TabController]
    with a [TabBar] and a [TabBarView].
    """
    widget_type = "DefaultTabController"

    def __init__(
        self,
        length: int,
        child: Widget,
        *,
        initial_index: int = 0,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            length=length,
            initial_index=initial_index,
            raw_props=raw_props,
        )
        self.children.append(child)


class Drawer(Widget):
    """
    A Material Design panel that slides in horizontally from the edge of a Scaffold
    to show navigation links in an application.
    """
    widget_type = "Drawer"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        background_color: Optional[str] = None,
        elevation: Optional[float] = 16.0,
        width: Optional[float] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            background_color=background_color,
            elevation=elevation,
            width=width,
            raw_props=raw_props,
        )
        if child is not None:
            self.children.append(child)


class DrawerHeader(Widget):
    """
    The top part of a Material Design Drawer, often containing an avatar, title,
    and background color or image.
    """
    widget_type = "DrawerHeader"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        background_color: Optional[str] = None,
        margin: Optional[float] = 12.0,
        padding: Optional[float] = 16.0,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            background_color=background_color,
            margin=margin,
            padding=padding,
            raw_props=raw_props,
        )
        if child is not None:
            self.children.append(child)


class BottomSheet(Widget):
    """
    A Material Design bottom sheet that slides up from the bottom of the screen.
    """
    widget_type = "BottomSheet"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        background_color: Optional[str] = None,
        elevation: Optional[float] = 8.0,
        border_radius: Optional[float] = 16.0,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            background_color=background_color,
            elevation=elevation,
            border_radius=border_radius,
            raw_props=raw_props,
        )
        if child is not None:
            self.children.append(child)


class MaterialApp(Widget):
    """
    An application that uses Material Design.
    Configures the root application title, Material 3 ThemeData, dark theme,
    ThemeMode, and home widget.

    Parameters:
        home: The primary screen/widget to display as the root.
        title: The title of the application displayed in OS task switchers.
        theme: Light theme configuration (ThemeData).
        dark_theme: Dark theme configuration (ThemeData).
        theme_mode: 'system' (adapts to OS), 'light', or 'dark'.
        debug_show_checked_mode_banner: Whether to show the debug ribbon.
    """
    widget_type = "MaterialApp"

    def __init__(
        self,
        home: Optional[Widget] = None,
        *,
        title: str = "PyFlutter",
        theme: Optional[ThemeData] = None,
        dark_theme: Optional[ThemeData] = None,
        theme_mode: str = "system",
        debug_show_checked_mode_banner: bool = False,
        routes: Optional[dict[str, Any]] = None,
        initial_route: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        props: dict[str, Any] = {
            "title": title,
            "theme_mode": theme_mode,
            "debug_banner": debug_show_checked_mode_banner,
        }
        if theme is not None:
            props.update(theme.to_props(prefix="theme_"))
            if theme.color_scheme and theme.color_scheme.seed_color:
                props["seed_color"] = theme.color_scheme.seed_color
        if dark_theme is not None:
            props.update(dark_theme.to_props(prefix="dark_theme_"))

        super().__init__(raw_props=raw_props, **props)

        from pyflutter.core.navigation import Navigator
        if routes:
            Navigator.set_routes(routes)

        effective_home = home
        if initial_route and routes and initial_route in routes:
            builder = routes[initial_route]
            effective_home = builder()

        self._initial_home = effective_home
        if effective_home is not None:
            Navigator.set_initial_page(effective_home)
        self._children_list: list[Widget] = []

    @property
    def children(self) -> list[Widget]:
        from pyflutter.core.navigation import Navigator
        if Navigator.can_pop():
            active = Navigator.current_page()
        else:
            active = self._initial_home or Navigator.current_page()
        if active is not None:
            active.props["slot"] = "home"
            return [active]
        return self._children_list

    @children.setter
    def children(self, val: list[Widget]):
        self._children_list = val


# --- 7. Additional Material & High-Value Components ---------------------------

class GridView(Widget):
    """
    A 2-dimensional, scrollable grid of widgets.
    """
    widget_type = "GridView"

    def __init__(
        self,
        children: Optional[Sequence[Widget]] = None,
        *,
        cross_axis_count: int = 2,
        main_axis_spacing: float = 8.0,
        cross_axis_spacing: float = 8.0,
        child_aspect_ratio: float = 1.0,
        shrink_wrap: bool = False,
        physics: Optional[str] = None,
        padding: Optional[float] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            cross_axis_count=cross_axis_count,
            main_axis_spacing=main_axis_spacing,
            cross_axis_spacing=cross_axis_spacing,
            child_aspect_ratio=child_aspect_ratio,
            shrink_wrap=shrink_wrap,
            physics=physics,
            padding=padding,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if children:
            self.children.extend(children)

    @classmethod
    def count(
        cls,
        cross_axis_count: int,
        children: Sequence[Widget],
        *,
        main_axis_spacing: float = 8.0,
        cross_axis_spacing: float = 8.0,
        child_aspect_ratio: float = 1.0,
        shrink_wrap: bool = False,
        padding: Optional[float] = None,
        **kwargs: Any,
    ) -> GridView:
        return cls(
            children=children,
            cross_axis_count=cross_axis_count,
            main_axis_spacing=main_axis_spacing,
            cross_axis_spacing=cross_axis_spacing,
            child_aspect_ratio=child_aspect_ratio,
            shrink_wrap=shrink_wrap,
            padding=padding,
            **kwargs,
        )


class Radio(Widget):
    """
    A Material Design radio button.
    Used to select between mutually exclusive options.
    """
    widget_type = "Radio"

    def __init__(
        self,
        value: Any,
        group_value: Any,
        *,
        on_change: Optional[Callable[[Any], None]] = None,
        on_changed: Optional[Callable[[Any], None]] = None,
        active_color: Optional[str] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            value=str(value),
            group_value=str(group_value),
            active_color=active_color,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        handler = on_changed or on_change
        if handler is not None:
            self.changed.connect(handler)

    @property
    def changed(self) -> QtSignal:
        if not hasattr(self, "_changed_signal"):
            self._changed_signal = QtSignal(self, "callback_id")
        return self._changed_signal


class RadioListTile(Widget):
    """
    A ListTile containing a radio button, title, and optional subtitle.
    """
    widget_type = "RadioListTile"

    def __init__(
        self,
        value: Any,
        group_value: Any,
        *,
        title: Any = "",
        subtitle: Optional[Any] = None,
        on_change: Optional[Callable[[Any], None]] = None,
        on_changed: Optional[Callable[[Any], None]] = None,
        active_color: Optional[str] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            value=str(value),
            group_value=str(group_value),
            active_color=active_color,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        title_w = title if isinstance(title, Widget) else Text(str(title))
        title_w.props["slot"] = "title"
        self.children.append(title_w)

        if subtitle is not None:
            sub_w = subtitle if isinstance(subtitle, Widget) else Text(str(subtitle))
            sub_w.props["slot"] = "subtitle"
            self.children.append(sub_w)

        handler = on_changed or on_change
        if handler is not None:
            self.changed.connect(handler)

    @property
    def changed(self) -> QtSignal:
        if not hasattr(self, "_changed_signal"):
            self._changed_signal = QtSignal(self, "callback_id")
        return self._changed_signal


class Tooltip(Widget):
    """
    A Material Design tooltip that displays informative text when pressed or hovered.
    """
    widget_type = "Tooltip"

    def __init__(
        self,
        message: str,
        child: Widget,
        *,
        wait_duration_ms: Optional[int] = None,
        show_duration_ms: Optional[int] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            message=message,
            wait_duration_ms=wait_duration_ms,
            show_duration_ms=show_duration_ms,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        self.children.append(child)


class TextSpan(Widget):
    """
    An immutable span of text with an individual style within a RichText tree.
    """
    widget_type = "TextSpan"

    def __init__(
        self,
        text: str = "",
        *,
        style: Optional[str | TextStyle] = None,
        font_size: Optional[float] = None,
        font_weight: Optional[str] = None,
        color: Optional[str] = None,
        font_style: Optional[str] = None,
        children: Optional[Sequence[TextSpan]] = None,
        on_click: Optional[Callable[[], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            text=text,
            font_size=font_size,
            font_weight=font_weight,
            color=color,
            font_style=font_style,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_click is not None:
            self.callback_id = _register_callback(on_click)
        if children:
            self.children.extend(children)


class RichText(Widget):
    """
    Displays text that uses multiple different styles in a single paragraph.
    """
    widget_type = "RichText"

    def __init__(
        self,
        spans: Sequence[TextSpan],
        *,
        text_align: Optional[str] = None,
        overflow: Optional[str] = None,
        max_lines: Optional[int] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            text_align=text_align,
            overflow=overflow,
            max_lines=max_lines,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        self.children.extend(spans)


class CircleAvatar(Widget):
    """
    A circular avatar displaying a user profile image or initials.
    """
    widget_type = "CircleAvatar"

    def __init__(
        self,
        child: Optional[Widget] = None,
        *,
        radius: Optional[float] = None,
        background_color: Optional[str] = None,
        foreground_color: Optional[str] = None,
        image_url: Optional[str] = None,
        on_click: Optional[Callable[[], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            radius=radius,
            background_color=background_color,
            foreground_color=foreground_color,
            image_url=image_url,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_click is not None:
            self.callback_id = _register_callback(on_click)
        if child:
            self.children.append(child)


class LinearProgressIndicator(Widget):
    """
    A Material Design linear progress bar.
    """
    widget_type = "LinearProgressIndicator"

    def __init__(
        self,
        value: Optional[float] = None,
        *,
        color: Optional[str] = None,
        background_color: Optional[str] = None,
        min_height: Optional[float] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            value=value,
            color=color,
            background_color=background_color,
            min_height=min_height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )


class PopupMenuItem(Widget):
    """
    An item inside a PopupMenuButton.
    """
    widget_type = "PopupMenuItem"

    def __init__(
        self,
        value: Any,
        child: Widget | str,
        *,
        enabled: bool = True,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            value=str(value),
            enabled=enabled,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        c = child if isinstance(child, Widget) else Text(str(child))
        self.children.append(c)


class PopupMenuButton(Widget):
    """
    Displays a menu when pressed and calls on_selected when an item is chosen.
    """
    widget_type = "PopupMenuButton"

    def __init__(
        self,
        items: Sequence[PopupMenuItem],
        *,
        on_selected: Optional[Callable[[str], None]] = None,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            icon=icon,
            tooltip=tooltip,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        self.children.extend(items)
        if on_selected is not None:
            self.selected.connect(on_selected)

    @property
    def selected(self) -> QtSignal:
        if not hasattr(self, "_selected_signal"):
            self._selected_signal = QtSignal(self, "callback_id")
        return self._selected_signal


class RefreshIndicator(Widget):
    """
    A widget that supports the Material 'swipe down to refresh' pull gesture.
    """
    widget_type = "RefreshIndicator"

    def __init__(
        self,
        child: Widget,
        *,
        on_refresh: Optional[Callable[[], None]] = None,
        color: Optional[str] = None,
        background_color: Optional[str] = None,
        displacement: float = 40.0,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            color=color,
            background_color=background_color,
            displacement=displacement,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        self.children.append(child)
        if on_refresh is not None:
            self.callback_id = _register_callback(on_refresh)


class AlertDialog(Widget):
    """
    A Material Design modal alert dialog.
    """
    widget_type = "AlertDialog"

    def __init__(
        self,
        title: Any = "",
        content: Any = "",
        *,
        actions: Optional[Sequence[Widget]] = None,
        background_color: Optional[str] = None,
        elevation: Optional[float] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            background_color=background_color,
            elevation=elevation,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        title_w = title if isinstance(title, Widget) else Text(str(title), style="titleLarge")
        title_w.props["slot"] = "title"
        self.children.append(title_w)

        content_w = content if isinstance(content, Widget) else Text(str(content))
        content_w.props["slot"] = "content"
        self.children.append(content_w)

        if actions:
            for a in actions:
                a.props["slot"] = "action"
                self.children.append(a)


class SimpleDialog(Widget):
    """
    A simple modal dialog offering choices to the user.
    """
    widget_type = "SimpleDialog"

    def __init__(
        self,
        title: Any = "",
        children: Optional[Sequence[Widget]] = None,
        *,
        background_color: Optional[str] = None,
        elevation: Optional[float] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            background_color=background_color,
            elevation=elevation,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        title_w = title if isinstance(title, Widget) else Text(str(title), style="titleLarge")
        title_w.props["slot"] = "title"
        self.children.append(title_w)

        if children:
            self.children.extend(children)


class WebView(Widget):
    """
    An in-app web browser widget.
    Can be controlled via a WebViewController or loaded with a static URL/HTML.
    """
    widget_type = "WebView"

    def __init__(
        self,
        url: str = "about:blank",
        *,
        controller: Optional[Any] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        show_address_bar: bool = True,
        on_navigation: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        ctrl_id = getattr(controller, "view_id", None) if controller else None
        target_url = getattr(controller, "_current_url", url) if controller else url
        super().__init__(
            url=str(target_url),
            view_id=ctrl_id,
            width=width,
            height=height,
            show_address_bar=show_address_bar,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_navigation:
            self.navigation.connect(on_navigation)

    @property
    def navigation(self) -> QtSignal:
        if not hasattr(self, "_navigation_signal"):
            self._navigation_signal = QtSignal(self, "callback_id")
        return self._navigation_signal


class VideoPlayer(Widget):
    """
    A video player widget displaying video streams, files, or assets.
    """
    widget_type = "VideoPlayer"

    def __init__(
        self,
        url_or_controller: Any,
        *,
        auto_play: bool = False,
        show_controls: bool = True,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_player_event: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        if hasattr(url_or_controller, "url"):
            url = getattr(url_or_controller, "url")
            ctrl_id = getattr(url_or_controller, "controller_id", None)
        else:
            url = str(url_or_controller)
            ctrl_id = None

        super().__init__(
            url=url,
            controller_id=ctrl_id,
            auto_play=auto_play,
            show_controls=show_controls,
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_player_event:
            self.player_event.connect(on_player_event)

    @property
    def player_event(self) -> QtSignal:
        if not hasattr(self, "_player_event_signal"):
            self._player_event_signal = QtSignal(self, "callback_id")
        return self._player_event_signal


class CameraPreview(Widget):
    """
    A live camera viewfinder widget for displaying camera previews.
    """
    widget_type = "CameraPreview"

    def __init__(
        self,
        controller_or_camera_id: Any = "0",
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_shutter: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        cam_id = getattr(controller_or_camera_id, "camera_id", str(controller_or_camera_id))
        super().__init__(
            camera_id=str(cam_id),
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_shutter:
            self.shutter.connect(on_shutter)

    @property
    def shutter(self) -> QtSignal:
        if not hasattr(self, "_shutter_signal"):
            self._shutter_signal = QtSignal(self, "callback_id")
        return self._shutter_signal


class Chewie(Widget):
    """
    An enhanced video player widget with Material/Cupertino controls and aspect ratio.
    """
    widget_type = "Chewie"

    def __init__(
        self,
        controller: Any,
        *,
        auto_play: bool = False,
        aspect_ratio: float = 16.0 / 9.0,
        show_controls: bool = True,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_event: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        video_ctrl = getattr(controller, "video_player_controller", controller)
        url = getattr(video_ctrl, "url", str(video_ctrl))
        ctrl_id = getattr(video_ctrl, "controller_id", None)
        auto_play_val = getattr(controller, "auto_play", auto_play)
        aspect_val = getattr(controller, "aspect_ratio", aspect_ratio)

        super().__init__(
            url=url,
            controller_id=ctrl_id,
            auto_play=auto_play_val,
            aspect_ratio=aspect_val,
            show_controls=show_controls,
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_event:
            self.event.connect(on_event)

    @property
    def event(self) -> QtSignal:
        if not hasattr(self, "_event_signal"):
            self._event_signal = QtSignal(self, "callback_id")
        return self._event_signal


class SfPdfViewer(Widget):
    """
    Syncfusion enterprise PDF viewer widget.
    Supports network URLs, local files, and asset documents with page navigation and zoom.
    """
    widget_type = "SfPdfViewer"

    def __init__(
        self,
        src: str,
        *,
        controller: Optional[Any] = None,
        can_show_pagination: bool = True,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_page_changed: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            src=str(src),
            can_show_pagination=can_show_pagination,
            page=getattr(controller, "current_page", None),
            zoom=getattr(controller, "zoom_level", None),
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_page_changed:
            self.page_changed.connect(on_page_changed)

    @classmethod
    def network(cls, url: str, **kwargs: Any) -> SfPdfViewer:
        return cls(url, **kwargs)

    @classmethod
    def file(cls, path: str, **kwargs: Any) -> SfPdfViewer:
        return cls(path, **kwargs)

    @classmethod
    def asset(cls, asset_name: str, **kwargs: Any) -> SfPdfViewer:
        return cls(asset_name, **kwargs)

    @property
    def page_changed(self) -> QtSignal:
        if not hasattr(self, "_page_changed_signal"):
            self._page_changed_signal = QtSignal(self, "callback_id")
        return self._page_changed_signal


class PdfView(Widget):
    """
    Modern PDFX document viewer widget with pinch-to-zoom and swipe page indicators.
    """
    widget_type = "PdfView"

    def __init__(
        self,
        path_or_controller: Any,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_page_changed: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        document = getattr(path_or_controller, "document", None)
        path = getattr(document, "path", None) or getattr(path_or_controller, "path", str(path_or_controller))
        super().__init__(
            path=str(path),
            page=getattr(path_or_controller, "current_page", None),
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_page_changed:
            self.page_changed.connect(on_page_changed)

    @property
    def page_changed(self) -> QtSignal:
        if not hasattr(self, "_page_changed_signal"):
            self._page_changed_signal = QtSignal(self, "callback_id")
        return self._page_changed_signal


class PdfViewPinch(PdfView):
    """Alias for PdfView with pinch-zoom support."""
    widget_type = "PdfViewPinch"


class PDFView(Widget):
    """
    Native platform PDF viewer (flutter_pdfview).
    """
    widget_type = "PDFView"

    def __init__(
        self,
        file_path: str,
        *,
        controller: Optional[Any] = None,
        enable_swipe: bool = True,
        swipe_horizontal: bool = False,
        width: Optional[float] = None,
        height: Optional[float] = None,
        on_page_changed: Optional[Callable[[dict[str, Any]], None]] = None,
        key: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            file_path=str(file_path),
            page=getattr(controller, "current_page", None),
            enable_swipe=enable_swipe,
            swipe_horizontal=swipe_horizontal,
            width=width,
            height=height,
            key=key,
            raw_props=raw_props,
            **kwargs,
        )
        if on_page_changed:
            self.page_changed.connect(on_page_changed)

    @property
    def page_changed(self) -> QtSignal:
        if not hasattr(self, "_page_changed_signal"):
            self._page_changed_signal = QtSignal(self, "callback_id")
        return self._page_changed_signal




