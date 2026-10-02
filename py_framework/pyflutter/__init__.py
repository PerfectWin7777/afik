"""
PyFlutter: Modern Python framework for building native cross-platform mobile apps with Flutter.
"""

from __future__ import annotations

# ============================================================================
# 1. Core & Application Lifecycle
# ============================================================================
from pyflutter.core.widget_base import (
    Widget,
    Component,
    StatelessWidget,
    QtSignal,
    MainWindow,
)
from pyflutter.core.navigation import Navigator
from pyflutter.core.logger import logger
from pyflutter.app import run, update

# ============================================================================
# 2. Design System, Material 3 Styling & Typography
# ============================================================================
from pyflutter.core.constants import (
    Icons,
    Colors,
    MainAxisAlignment,
    CrossAxisAlignment,
    FontWeight,
    TextAlign,
    BoxFit,
    FlexFit,
    WrapAlignment,
    Axis,
    Curves,
    HitTestBehavior,
    DismissDirection,
    Alignment,
    MainAxisSize,
    FloatingActionButtonLocation,
    ScrollPhysics,
)
from pyflutter.core.style import (
    Duration,
    TextStyle,
    FontStyle,
    TextDecoration,
    TextOverflow,
    ColorScheme,
    ThemeData,
    ThemeMode,
    TextTheme,
)
from pyflutter.plugins.overlay import show_snack_bar, show_dialog
from pyflutter import plugins


# ============================================================================
# 3. Forms, Controllers & Validation
# ============================================================================
from pyflutter.core.form import (
    Form,
    FormKey,
    TextEditingController,
    Validators,
    InputBorder,
    OutlineInputBorder,
    UnderlineInputBorder,
)

# ============================================================================
# 4. Reactive State Management
# ============================================================================
from pyflutter.core.state import (
    Signal,
    ValueNotifier,
    Computed,
    Effect,
    batch,
    Watch,
    SignalBuilder,
    ValueListenableBuilder,
    StatefulComponent,
    StatefulWidget,
    State,
)

# ============================================================================
# 5. Gestures, Touch & Animations
# ============================================================================
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

# ============================================================================
# 6. Material & Layout Widgets
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
    VerticalDivider,
    SafeArea,
    Row,
    Column,
    Wrap,
    Stack,
    Positioned,
    Flexible,
    FittedBox,

    # Basic UI & Media
    Text,
    Image,
    Icon,
    IconButton,
    Button,
    ElevatedButton,
    OutlinedButton,
    TextButton,
    FloatingActionButton,
    Badge,
    Chip,
    ActionChip,
    TextField,
    TextFormField,
    DropdownButton,
    DropdownMenuItem,
    DropdownMenu,
    Switch,
    Checkbox,
    Slider,
    CircularProgressIndicator,

    # Scrollables & Collections
    ListView,
    ListTile,
    SingleChildScrollView,
    GridView,
    RefreshIndicator,

    # High-Value Material Controls
    Radio,
    RadioListTile,
    Tooltip,
    TextSpan,
    RichText,
    CircleAvatar,
    LinearProgressIndicator,
    PopupMenuItem,
    PopupMenuButton,
    AlertDialog,
    SimpleDialog,

    # Application Shell, Material 3 & Navigation
    MaterialApp,
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
    "logger",
    "Navigator",
    "Widget",
    "Component",
    "StatelessWidget",
    "MainWindow",
    "QtSignal",
    "plugins",


    # Reactive State Management
    "Signal",
    "ValueNotifier",
    "Computed",
    "Effect",
    "batch",
    "Watch",
    "SignalBuilder",
    "ValueListenableBuilder",
    "StatefulComponent",
    "StatefulWidget",
    "State",

    # Gestures & Touch
    "GestureDetector",
    "InkWell",
    "Dismissible",

    # Animations & Transitions
    "Hero",
    "AnimatedContainer",
    "AnimatedOpacity",
    "AnimatedScale",
    "AnimatedRotation",
    "AnimatedAlign",
    "AnimatedCrossFade",

    # Material 3 Styling & Typography
    "Duration",
    "TextStyle",
    "FontStyle",
    "TextDecoration",
    "TextOverflow",
    "ColorScheme",
    "ThemeData",
    "ThemeMode",
    "TextTheme",

    # Overlays & Feedback
    "show_snack_bar",
    "show_dialog",

    # Forms & Validation
    "Form",
    "FormKey",
    "TextEditingController",
    "Validators",
    "InputBorder",
    "OutlineInputBorder",
    "UnderlineInputBorder",

    # Styling & Constants
    "Icons",
    "Colors",
    "MainAxisAlignment",
    "CrossAxisAlignment",
    "MainAxisSize",
    "FontWeight",
    "TextAlign",
    "BoxFit",
    "FlexFit",
    "WrapAlignment",
    "Axis",
    "Curves",
    "HitTestBehavior",
    "DismissDirection",
    "Alignment",
    "FloatingActionButtonLocation",
    "ScrollPhysics",

    # Layout Widgets
    "Row",
    "Column",
    "Wrap",
    "Stack",
    "Positioned",
    "Flexible",
    "FittedBox",
    "Container",
    "Card",
    "Padding",
    "SizedBox",
    "Center",
    "Expanded",
    "Spacer",
    "Divider",
    "VerticalDivider",
    "SafeArea",

    # Basic UI & Interactive Controls
    "Text",
    "Image",
    "Icon",
    "IconButton",
    "Button",
    "ElevatedButton",
    "OutlinedButton",
    "TextButton",
    "FloatingActionButton",
    "Badge",
    "Chip",
    "ActionChip",
    "TextField",
    "TextFormField",
    "DropdownButton",
    "DropdownMenuItem",
    "DropdownMenu",
    "Switch",
    "Checkbox",
    "Slider",
    "CircularProgressIndicator",

    # Scrollable & Navigation
    "MaterialApp",
    "ListView",
    "ListTile",
    "SingleChildScrollView",
    "GridView",
    "RefreshIndicator",
    "Radio",
    "RadioListTile",
    "Tooltip",
    "TextSpan",
    "RichText",
    "CircleAvatar",
    "LinearProgressIndicator",
    "PopupMenuItem",
    "PopupMenuButton",
    "AlertDialog",
    "SimpleDialog",
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
