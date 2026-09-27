"""
PyFlutter: Modern Python framework for building native cross-platform mobile apps with Flutter.
"""

from __future__ import annotations

# ============================================================================
# 1. Core & Application Lifecycle
# ============================================================================
from pyflutter.core.widget_base import Widget, Component, StatelessWidget
from pyflutter.app import run, update

# ============================================================================
# 2. Design System & Layout Constants
# ============================================================================
from pyflutter.core.constants import (
    Icons,
    Colors,
    MainAxisAlignment,
    CrossAxisAlignment,
    FontWeight,
    TextAlign,
    BoxFit,
)

# ============================================================================
# 3. Material & Layout Widgets
# ============================================================================
from pyflutter.widgets.widgets import (
    # Structural Layout
    Container,
    Card,
    Padding,
    SizedBox,
    Center,
    Expanded,
    Spacer,
    Divider,
    SafeArea,
    Row,
    Column,
    Stack,
    Positioned,

    # Basic UI & Media
    Text,
    Image,
    Icon,
    IconButton,
    Button,
    TextField,
    Switch,
    Checkbox,
    CircularProgressIndicator,

    # Scrollables & Collections
    ListView,
    SingleChildScrollView,

    # Application Shell & Navigation
    Scaffold,
    AppBar,
    Drawer,
    DrawerHeader,
    BottomSheet,
    BottomNavigationBar,
    BottomNavigationBarItem,
    PageView,
    Tab,
    TabBar,
    TabBarView,
    DefaultTabController,
)

__version__ = "0.1.0"

__all__ = [
    # Application & State
    "run",
    "update",
    "Widget",
    "Component",
    "StatelessWidget",

    # Styling & Constants
    "Icons",
    "Colors",
    "MainAxisAlignment",
    "CrossAxisAlignment",
    "FontWeight",
    "TextAlign",
    "BoxFit",

    # Layout Widgets
    "Row",
    "Column",
    "Stack",
    "Positioned",
    "Container",
    "Card",
    "Padding",
    "SizedBox",
    "Center",
    "Expanded",
    "Spacer",
    "Divider",
    "SafeArea",

    # Basic UI Widgets
    "Text",
    "Image",
    "Icon",
    "IconButton",
    "Button",
    "TextField",
    "Switch",
    "Checkbox",
    "CircularProgressIndicator",

    # Scrollable & Navigation
    "ListView",
    "SingleChildScrollView",
    "Scaffold",
    "AppBar",
    "Drawer",
    "DrawerHeader",
    "BottomSheet",
    "BottomNavigationBar",
    "BottomNavigationBarItem",
    "PageView",
    "Tab",
    "TabBar",
    "TabBarView",
    "DefaultTabController",
]
