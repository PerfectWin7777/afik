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
    WebView,
    VideoPlayer,
    CameraPreview,
    Chewie,

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

# ============================================================================
# 7. Native Hardware, Media & Device Plugins
# ============================================================================
from pyflutter.plugins.image_picker import ImagePicker, XFile, ImageSource
from pyflutter.plugins.camera import CameraController, CameraDescription, available_cameras
from pyflutter.plugins.connectivity import ConnectivityResult, check_connectivity, is_connected
from pyflutter.plugins.audioplayer import AudioPlayer, PlayerState
from pyflutter.plugins.video_player import VideoPlayerController
from pyflutter.plugins.share import share, share_files
from pyflutter.plugins.webview import WebViewController
from pyflutter.plugins.chewie import ChewieController
from pyflutter.plugins.hive import Box, open_box
from pyflutter.plugins.sqflite import Database, open_database
from pyflutter.plugins.local_notifications import FlutterLocalNotificationsPlugin
from pyflutter.plugins.permission_handler import Permission, PermissionStatus, check_permission, request_permission
from pyflutter.plugins.secure_storage import FlutterSecureStorage
from pyflutter.plugins.local_auth import LocalAuthentication



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
    "WebView",
    "VideoPlayer",
    "CameraPreview",
    "Chewie",
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

    # Native Plugins & Hardware
    "ImagePicker",
    "XFile",
    "ImageSource",
    "CameraController",
    "CameraDescription",
    "available_cameras",
    "ConnectivityResult",
    "check_connectivity",
    "is_connected",
    "AudioPlayer",
    "PlayerState",
    "VideoPlayerController",
    "WebViewController",
    "share",
    "share_files",
    "ChewieController",
    "Box",
    "open_box",
    "Database",
    "open_database",
    "FlutterLocalNotificationsPlugin",
    "Permission",
    "PermissionStatus",
    "check_permission",
    "request_permission",
    "FlutterSecureStorage",
    "LocalAuthentication",
]


