"""
PyFlutter Widget Collection.
Fully-typed, documented widgets with complete IDE hover, autocomplete, and docstrings.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

from pyflutter.core.widget_base import Widget, _register_callback
from pyflutter.core.constants import Axis, BoxFit, FlexFit, WrapAlignment


# --- 1. Typography & Display --------------------------------------------------

class Text(Widget):
    """
    A run of text with styled font, weight, color, alignment and truncation.

    Parameters:
        value: The text string to display.
        font_size: Size of the text in logical pixels (e.g. 14, 18.5).
        font_weight: Thickness of the glyphs ('normal', 'bold', 'w600').
        color: Hex color string (e.g. '#1877F2', '#000000').
        raw_props: Escape hatch dictionary for unmapped Flutter properties.
    """
    widget_type = "Text"

    def __init__(self, value: Any = "", *,
                 font_size: Optional[int | float] = None,
                 font_weight: Optional[str] = None,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            value=str(value),
            font_size=font_size,
            font_weight=font_weight,
            color=color,
            raw_props=raw_props,
        )

    def set_text(self, value: Any) -> Text:
        """Dynamically updates the text content."""
        self.props["value"] = str(value)
        return self


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
    widget_type = "Icon"

    def __init__(self, name: str, *,
                 on_click: Callable,
                 size: Optional[int | float] = None,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            name=name,
            size=size,
            color=color,
            raw_props=raw_props,
        )
        self.callback_id = _register_callback(on_click)


# --- 2. Layout & Containers ---------------------------------------------------

class Column(Widget):
    """
    A widget that displays its children in a vertical array.

    Parameters:
        children: List of child widgets to arrange vertically.
        main_axis_alignment: How children align along the vertical axis ('start', 'center', 'space_between').
        cross_axis_alignment: How children align along the horizontal axis ('start', 'center', 'stretch').
    """
    widget_type = "Column"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 main_axis_alignment: Optional[str] = None,
                 cross_axis_alignment: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
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
    """
    widget_type = "Row"

    def __init__(self, children: Optional[Sequence[Widget]] = None, *,
                 main_axis_alignment: Optional[str] = None,
                 cross_axis_alignment: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
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
                 color: Optional[str] = None,
                 width: Optional[int | float] = None,
                 height: Optional[int | float] = None,
                 border_radius: Optional[int | float] = None,
                 on_click: Optional[Callable] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            padding=padding,
            color=color,
            width=width,
            height=height,
            border_radius=border_radius,
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
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            padding=padding,
            elevation=elevation,
            margin=margin,
            border_radius=border_radius,
            color=color,
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
                 horizontal: Optional[int | float] = None,
                 vertical: Optional[int | float] = None,
                 top: Optional[int | float] = None,
                 bottom: Optional[int | float] = None,
                 left: Optional[int | float] = None,
                 right: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            all=all,
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
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            height=height,
            thickness=thickness,
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
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(padding=padding, raw_props=raw_props)
        self.children = list(children) if children else []


class SingleChildScrollView(Widget):
    """
    A box in which a single widget can be scrolled.

    Parameters:
        child: The single widget to scroll.
        scroll_direction: Direction of scroll ('vertical' or 'horizontal'). Default is 'vertical'.
        padding: Padding inside the scroll view.
    """
    widget_type = "SingleChildScrollView"

    def __init__(self, child: Widget, *,
                 scroll_direction: str = Axis.VERTICAL,
                 padding: Optional[int | float] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            scroll_direction=scroll_direction,
            padding=padding,
            raw_props=raw_props,
        )
        self.children = [child]


# --- 4. Inputs & Interactive Controls -----------------------------------------

class Button(Widget):
    """
    An elevated Material button with optional icon, label, and click callback.
    """
    widget_type = "Button"

    def __init__(self, label: Any = "", *,
                 icon: Optional[str] = None,
                 on_click: Optional[Callable] = None,
                 color: Optional[str] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            label=str(label),
            icon=icon,
            color=color,
            raw_props=raw_props,
        )
        if on_click is not None:
            self.callback_id = _register_callback(on_click)

    def on_click(self, fn: Callable) -> Button:
        self.callback_id = _register_callback(fn)
        return self


class TextField(Widget):
    """
    A Material text field for user text input.
    """
    widget_type = "TextField"

    def __init__(self, value: str = "", *,
                 placeholder: Optional[str] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 raw_props: Optional[dict[str, Any]] = None):
        super().__init__(
            value=str(value),
            placeholder=placeholder,
            raw_props=raw_props,
        )
        if on_change is not None:
            self.callback_id = _register_callback(on_change)

    def set_value(self, value: str) -> TextField:
        self.props["value"] = str(value)
        return self


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
            self.callback_id = _register_callback(on_change)


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
            self.callback_id = _register_callback(on_change)


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
        center_title: Optional[bool] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            title=title if isinstance(title, str) else None,
            background_color=background_color,
            elevation=elevation,
            center_title=center_title,
            raw_props=raw_props,
        )
        if isinstance(title, Widget):
            title.props["slot"] = "title"
            self.children.append(title)
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
        drawer: Optional[Widget] = None,
        end_drawer: Optional[Widget] = None,
        bottom_sheet: Optional[Widget] = None,
        background_color: Optional[str] = None,
        raw_props: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            background_color=background_color,
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
