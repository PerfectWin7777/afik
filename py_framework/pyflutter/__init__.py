"""
PyFlutter: Modern Python framework for building native cross-platform mobile apps with Flutter.
"""

from __future__ import annotations

import importlib
from typing import Any

from pyflutter import plugins
from pyflutter.app import run, run_on_ui, update

# ============================================================================
# 7. MethodChannel & Platform Communication
# ============================================================================
from pyflutter.core.channel import (
    EventChannel,
    MethodCall,
    MethodChannel,
    PlatformException,
)

# ============================================================================
# 2. Design System, Material 3 Styling & Typography
# ============================================================================
from pyflutter.core.constants import (
    Alignment,
    Axis,
    BoxFit,
    BoxShape,
    Colors,
    CrossAxisAlignment,
    Curves,
    DismissDirection,
    FlexFit,
    FloatingActionButtonLocation,
    FontWeight,
    HitTestBehavior,
    Icons,
    MainAxisAlignment,
    MainAxisSize,
    ScrollPhysics,
    TextAlign,
    WrapAlignment,
)

# ============================================================================
# 3. Forms, Controllers & Validation
# ============================================================================
from pyflutter.core.form import (
    Form,
    FormKey,
    InputBorder,
    OutlineInputBorder,
    TextEditingController,
    UnderlineInputBorder,
    Validators,
)
from pyflutter.core.logger import logger
from pyflutter.core.navigation import Navigator

# ============================================================================
# 4. Reactive State Management
# ============================================================================
from pyflutter.core.state import (
    Computed,
    Effect,
    Signal,
    SignalBuilder,
    State,
    StatefulComponent,
    StatefulWidget,
    ValueListenableBuilder,
    ValueNotifier,
    Watch,
    batch,
)
from pyflutter.core.style import (
    ColorScheme,
    Duration,
    FontStyle,
    TextDecoration,
    TextOverflow,
    TextStyle,
    TextTheme,
    ThemeData,
    ThemeMode,
)

# ============================================================================
# 1. Core & Application Lifecycle
# ============================================================================
from pyflutter.core.widget_base import (
    Component,
    MainWindow,
    QtSignal,
    StatelessWidget,
    Widget,
)
from pyflutter.plugins.overlay import show_dialog, show_snack_bar
from pyflutter.widgets.animations import (
    AnimatedAlign,
    AnimatedContainer,
    AnimatedCrossFade,
    AnimatedOpacity,
    AnimatedRotation,
    AnimatedScale,
    Hero,
)

# ============================================================================
# 5. Gestures, Touch & Animations
# ============================================================================
from pyflutter.widgets.gestures import (
    Dismissible,
    GestureDetector,
    InkWell,
)

# ============================================================================
# 6. Material & Layout Widgets
# ============================================================================
from pyflutter.widgets.widgets import (
    ActionChip,
    AlertDialog,
    AppBar,
    Badge,
    BottomNavigationBar,
    BottomNavigationBarItem,
    BottomSheet,
    Button,
    CameraPreview,
    Card,
    Center,
    Checkbox,
    Chewie,
    Chip,
    CircleAvatar,
    CircularProgressIndicator,
    Column,
    # Structural Layout
    Container,
    DefaultTabController,
    Divider,
    Drawer,
    DrawerHeader,
    DropdownButton,
    DropdownMenu,
    DropdownMenuItem,
    ElevatedButton,
    Expanded,
    FittedBox,
    Flexible,
    FloatingActionButton,
    GridView,
    Icon,
    IconButton,
    Image,
    LinearProgressIndicator,
    ListTile,
    # Scrollables & Collections
    ListView,
    # Application Shell, Material 3 & Navigation
    MaterialApp,
    OutlinedButton,
    Padding,
    PageView,
    PDFView,
    PdfView,
    PdfViewPinch,
    PopupMenuButton,
    PopupMenuItem,
    Positioned,
    # High-Value Material Controls
    Radio,
    RadioListTile,
    RefreshIndicator,
    RichText,
    Row,
    SafeArea,
    Scaffold,
    SfPdfViewer,
    SimpleDialog,
    SingleChildScrollView,
    SizedBox,
    Slider,
    Spacer,
    Stack,
    Switch,
    Tab,
    TabBar,
    TabBarView,
    # Basic UI & Media
    Text,
    TextButton,
    TextField,
    TextFormField,
    TextSpan,
    Tooltip,
    VerticalDivider,
    VideoPlayer,
    WebView,
    Wrap,
)

_DEPRECATED_ROOT_EXPORTS: dict[str, tuple[str, str]] = {
    "ImagePicker": ("pyflutter.plugins.image_picker", "ImagePicker"),
    "XFile": ("pyflutter.plugins.image_picker", "XFile"),
    "ImageSource": ("pyflutter.plugins.image_picker", "ImageSource"),
    "CameraController": ("pyflutter.plugins.camera", "CameraController"),
    "CameraDescription": ("pyflutter.plugins.camera", "CameraDescription"),
    "available_cameras": ("pyflutter.plugins.camera", "available_cameras"),
    "CameraPreview": ("pyflutter.plugins.camera", "CameraPreview"),
    "ConnectivityResult": ("pyflutter.plugins.connectivity", "ConnectivityResult"),
    "check_connectivity": ("pyflutter.plugins.connectivity", "check_connectivity"),
    "is_connected": ("pyflutter.plugins.connectivity", "is_connected"),
    "AudioPlayer": ("pyflutter.plugins.audioplayer", "AudioPlayer"),
    "PlayerState": ("pyflutter.plugins.audioplayer", "PlayerState"),
    "VideoPlayerController": ("pyflutter.plugins.video_player", "VideoPlayerController"),
    "VideoPlayer": ("pyflutter.plugins.video_player", "VideoPlayer"),
    "share": ("pyflutter.plugins.share", "share"),
    "share_files": ("pyflutter.plugins.share", "share_files"),
    "WebViewController": ("pyflutter.plugins.webview", "WebViewController"),
    "WebView": ("pyflutter.plugins.webview", "WebView"),
    "ChewieController": ("pyflutter.plugins.chewie", "ChewieController"),
    "Chewie": ("pyflutter.plugins.chewie", "Chewie"),
    "Box": ("pyflutter.plugins.hive", "Box"),
    "open_box": ("pyflutter.plugins.hive", "open_box"),
    "Database": ("pyflutter.plugins.sqflite", "Database"),
    "open_database": ("pyflutter.plugins.sqflite", "open_database"),
    "FlutterLocalNotificationsPlugin": ("pyflutter.plugins.local_notifications", "FlutterLocalNotificationsPlugin"),
    "Permission": ("pyflutter.plugins.permission_handler", "Permission"),
    "PermissionStatus": ("pyflutter.plugins.permission_handler", "PermissionStatus"),
    "check_permission": ("pyflutter.plugins.permission_handler", "check_permission"),
    "request_permission": ("pyflutter.plugins.permission_handler", "request_permission"),
    "FlutterSecureStorage": ("pyflutter.plugins.secure_storage", "FlutterSecureStorage"),
    "LocalAuthentication": ("pyflutter.plugins.local_auth", "LocalAuthentication"),
    "SfPdfViewer": ("pyflutter.plugins.pdf", "SfPdfViewer"),
    "PdfView": ("pyflutter.plugins.pdf", "PdfView"),
    "PdfViewPinch": ("pyflutter.plugins.pdf", "PdfViewPinch"),
    "PDFView": ("pyflutter.plugins.pdf", "PDFView"),
    "PdfViewerController": ("pyflutter.plugins.pdf", "PdfViewerController"),
    "PdfDocument": ("pyflutter.plugins.pdf", "PdfDocument"),
    "Printing": ("pyflutter.plugins.pdf", "Printing"),
}

def __getattr__(name: str) -> Any:
    if name in _DEPRECATED_ROOT_EXPORTS:
        mod_name, attr_name = _DEPRECATED_ROOT_EXPORTS[name]
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr_name)
    raise AttributeError(f"module 'pyflutter' has no attribute '{name}'")


__version__ = "0.1.0"


__all__ = [
    "WebView",
    "VideoPlayer",
    "CameraPreview",
    "Chewie",
    "SfPdfViewer",
    "PdfView",
    "PdfViewPinch",
    "PDFView",
    # Application & State
    "run",
    "update",
    "run_on_ui",
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
    "BoxShape",
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

    # Platform Channels & Communication
    "MethodChannel",
    "EventChannel",
    "MethodCall",
    "PlatformException",
]



