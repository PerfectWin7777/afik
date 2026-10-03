"""
Standard constants and enums for PyFlutter applications.
Provides full IDE autocomplete for icons, colors, alignments, font weights, and common styles.
"""

from __future__ import annotations


class _IconsMeta(type):
    """
    Metaclass providing graceful dynamic fallback for any Material icon.
    If an icon attribute is not explicitly defined in the class, it automatically
    resolves the uppercase attribute to lowercase snake_case (e.g. Icons.OPEN_IN_NEW -> 'open_in_new'),
    preventing any unexpected AttributeError crashes while preserving IDE autocomplete.
    """
    def __getattr__(cls, name: str) -> str:
        return name.lower()


class Icons(metaclass=_IconsMeta):
    """
    Standard Material Design icon identifiers supported natively by the PyFlutter runtime.
    Using these constants enables full VS Code auto-completion and prevents runtime typos.
    """
    # Navigation & Actions
    HOME = "home"
    SETTINGS = "settings"
    SEARCH = "search"
    NOTIFICATIONS = "notifications"
    NOTIFICATIONS_OUTLINED = "notifications_outlined"
    MENU = "menu"
    MORE_VERT = "more_vert"
    MORE_HORIZ = "more_horiz"
    CLOSE = "close"
    ADD = "add"
    REMOVE = "remove"
    CHECK = "check"
    CHECK_CIRCLE = "check_circle"
    CHECK_CIRCLE_OUTLINE = "check_circle_outline"
    CANCEL = "cancel"
    ARROW_BACK = "arrow_back"
    ARROW_FORWARD = "arrow_forward"
    ARROW_UPWARD = "arrow_upward"
    ARROW_DOWNWARD = "arrow_downward"
    ARROW_DROP_DOWN = "arrow_drop_down"
    ARROW_DROP_UP = "arrow_drop_up"
    CHEVRON_LEFT = "chevron_left"
    CHEVRON_RIGHT = "chevron_right"
    EXPAND_MORE = "expand_more"
    EXPAND_LESS = "expand_less"
    REFRESH = "refresh"
    FILTER_LIST = "filter_list"
    SORT = "sort"
    EDIT = "edit"
    DELETE = "delete"
    DELETE_OUTLINE = "delete_outline"
    SHARE = "share"
    SHARE_OUTLINED = "share_outlined"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    VISIBILITY = "visibility"
    VISIBILITY_OFF = "visibility_off"
    HELP = "help"
    HELP_OUTLINE = "help_outline"
    INFO = "info"
    INFO_OUTLINE = "info_outline"
    WARNING = "warning"
    ERROR = "error"
    ERROR_OUTLINE = "error_outline"
    LOCK = "lock"
    LOCK_OPEN = "lock_open"
    OPEN_IN_NEW = "open_in_new"
    LAUNCH = "open_in_new"

    # Social & Communication
    THUMB_UP = "thumb_up"
    THUMB_UP_OUTLINED = "thumb_up_outlined"
    THUMB_DOWN = "thumb_down"
    THUMB_DOWN_OUTLINED = "thumb_down_outlined"
    FAVORITE = "favorite"
    FAVORITE_BORDER = "favorite_border"
    COMMENT = "comment"
    CHAT = "chat"
    CHAT_BUBBLE = "chat_bubble"
    CHAT_BUBBLE_OUTLINE = "chat_bubble_outline"
    SEND = "send"
    EMAIL = "email"
    EMAIL_OUTLINED = "email_outlined"
    PHONE = "phone"
    PERSON = "person"
    PERSON_OUTLINE = "person_outline"
    PEOPLE = "people"
    PUBLIC = "public"
    STAR = "star"
    STAR_BORDER = "star_border"
    STAR_HALF = "star_half"

    # E-commerce, Shopping & Finance
    SHOPPING_CART = "shopping_cart"
    SHOPPING_CART_OUTLINED = "shopping_cart_outlined"
    SHOPPING_BAG = "shopping_bag"
    SHOPPING_BAG_OUTLINED = "shopping_bag_outlined"
    STORE = "store"
    STOREFRONT = "storefront"
    PAYMENT = "payment"
    CREDIT_CARD = "credit_card"
    RECEIPT = "receipt"
    SELL = "sell"
    LOCAL_SHIPPING = "local_shipping"
    ACCOUNT_BALANCE_WALLET = "account_balance_wallet"
    SAVINGS = "savings"

    # Media & Content
    IMAGE = "image"
    PHOTO = "photo"
    CAMERA_ALT = "camera_alt"
    VIDEO_LIBRARY = "video_library"
    PLAY_ARROW = "play_arrow"
    PAUSE = "pause"
    STOP = "stop"
    SKIP_NEXT = "skip_next"
    SKIP_PREVIOUS = "skip_previous"
    VOLUME_UP = "volume_up"
    VOLUME_OFF = "volume_off"
    MIC = "mic"
    MUSIC_NOTE = "music_note"
    GRID_VIEW = "grid_view"
    LIST = "list"
    ARTICLE = "article"
    DESCRIPTION = "description"

    # Weather & Nature
    WB_SUNNY = "wb_sunny"
    CLOUD = "cloud"
    THUNDERSTORM = "thunderstorm"
    WATER_DROP = "water_drop"
    AC_UNIT = "ac_unit"
    AIR = "air"

    # Places & Devices
    LOCATION_ON = "location_on"
    MAP = "map"
    COMPUTER = "computer"
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    HEADPHONES = "headphones"
    WATCH = "watch"
    WIFI = "wifi"
    BATTERY_FULL = "battery_full"


class Colors:
    """
    Comprehensive color palette for rapid, consistent UI styling.
    Provides standard Material, Tailwind-compatible swatches, semantic tokens,
    and the with_opacity() helper for alpha channel calculations.
    """
    # Special & Transparents
    TRANSPARENT = "transparent"
    WHITE = "#FFFFFF"
    BLACK = "#000000"

    # Brand & Deep Primaries
    BLUE = "#1877F2"
    FACEBOOK_BLUE = "#1877F2"
    NAVY = "#1E3A8A"
    DEEP_BLUE = "#1E3A8A"
    LIGHT_BLUE = "#03A9F4"
    CYAN = "#00BCD4"
    TEAL = "#009688"
    INDIGO = "#3F51B5"
    INDIGO_500 = "#6366F1"
    PURPLE = "#7B1FA2"
    DEEP_PURPLE = "#673AB7"
    VIOLET = "#8B5CF6"
    VIOLET_600 = "#7C3AED"
    PINK = "#E91E63"
    ROSE = "#F43F5E"
    BROWN = "#795548"

    # Blue Scale
    BLUE_50 = "#EFF6FF"
    BLUE_100 = "#DBEAFE"
    BLUE_200 = "#BFDBFE"
    BLUE_300 = "#93C5FD"
    BLUE_400 = "#60A5FA"
    BLUE_500 = "#3B82F6"
    BLUE_600 = "#2563EB"
    BLUE_700 = "#1D4ED8"
    BLUE_800 = "#1E40AF"
    BLUE_900 = "#1E3A8A"

    # Greens & Emeralds
    GREEN = "#42B72A"
    GREEN_ACCENT = "#45BD62"
    LIGHT_GREEN = "#8BC34A"
    EMERALD = "#10B981"
    EMERALD_50 = "#ECFDF5"
    EMERALD_100 = "#D1FAE5"
    EMERALD_500 = "#10B981"
    EMERALD_600 = "#059669"
    EMERALD_700 = "#047857"

    # Ambers & Oranges
    AMBER = "#FFC107"
    AMBER_500 = "#F59E0B"
    AMBER_ACCENT = "#F7B125"
    ORANGE = "#FF9800"
    ORANGE_500 = "#F97316"
    DEEP_ORANGE = "#FF5722"

    # Reds
    RED = "#E41E3F"
    RED_500 = "#EF4444"
    RED_600 = "#DC2626"

    # Modern Slates (Cool Greys)
    SLATE_50 = "#F8FAFC"
    SLATE_100 = "#F1F5F9"
    SLATE_200 = "#E2E8F0"
    SLATE_300 = "#CBD5E1"
    SLATE_400 = "#94A3B8"
    SLATE_500 = "#64748B"
    SLATE_600 = "#475569"
    SLATE_700 = "#334155"
    SLATE_800 = "#1E293B"
    SLATE_900 = "#0F172A"

    # Greys & Neutrals
    GREY_50 = "#FAFAFA"
    GREY_100 = "#F5F5F5"
    GREY_200 = "#EEEEEE"
    GREY_300 = "#E0E0E0"
    GREY_400 = "#BDBDBD"
    GREY_500 = "#9E9E9E"
    GREY_600 = "#757575"
    GREY_700 = "#616161"
    GREY_800 = "#424242"
    GREY_900 = "#212121"

    # Common Aliases
    GREY = "#65676B"
    LIGHT_GREY = "#F0F2F5"
    BORDER_GREY = "#E4E6EB"
    DARK_GREY = "#1C1E21"

    # Semantic UI Layout & Typography Tokens
    SCAFFOLD_BACKGROUND = "#F8FAFC"
    CARD_BACKGROUND = "#FFFFFF"
    SURFACE = "#FFFFFF"
    BACKGROUND = "#F0F2F5"
    DIVIDER = "#E2E8F0"
    BORDER = "#E4E6EB"
    INPUT_BACKGROUND = "#F0F2F5"
    INPUT_FILL = "#F0F2F5"

    TEXT_PRIMARY = "#0F172A"
    TEXT_DARK = "#1C1E21"
    TEXT_SECONDARY = "#65676B"
    TEXT_MUTED = "#94A3B8"
    TEXT_LIGHT = "#FFFFFF"

    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    ERROR = "#EF4444"
    INFO = "#1877F2"

    @staticmethod
    def with_opacity(color: str, opacity: float) -> str:
        """
        Returns a hex color string with the specified opacity applied (0.0 to 1.0).
        Outputs #AARRGGBB formatted for native Flutter color parsing.
        Example:
            Colors.with_opacity(Colors.EMERALD, 0.15) -> '#2610B981'
        """
        if not color or color == "transparent":
            return "transparent"
        cl = color.lstrip("#")
        # Strip preexisting alpha if 8 characters
        if len(cl) == 8:
            cl = cl[2:]
        alpha_int = int(max(0.0, min(1.0, opacity)) * 255)
        return f"#{alpha_int:02X}{cl}"

    with_alpha = with_opacity


class MainAxisSize:
    """How much space should be occupied along the main axis in a Row or Column."""
    MIN = "min"
    MAX = "max"


class MainAxisAlignment:
    """Arrangement of children along the main axis of a Row or Column."""
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space_between"
    SPACE_AROUND = "space_around"
    SPACE_EVENLY = "space_evenly"


class CrossAxisAlignment:
    """Arrangement of children along the cross axis of a Row or Column."""
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"
    BASELINE = "baseline"


class FontWeight:
    """Thickness of the glyphs in a font."""
    NORMAL = "normal"
    BOLD = "bold"
    W100 = "w100"
    W200 = "w200"
    W300 = "w300"
    W400 = "w400"
    W500 = "w500"
    W600 = "w600"
    W700 = "w700"
    W800 = "w800"
    W900 = "w900"


class TextAlign:
    """Horizontal alignment of text within its bounding box."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"
    START = "start"
    END = "end"


class BoxFit:
    """How an image or fitted box should fit within its allocated space."""
    CONTAIN = "contain"
    COVER = "cover"
    FILL = "fill"
    FIT_WIDTH = "fit_width"
    FIT_HEIGHT = "fit_height"
    SCALE_DOWN = "scale_down"
    NONE = "none"


class BoxShape:
    """The shape to generate when painting a BoxDecoration or Container."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"


class FlexFit:
    """How the child of a Flexible widget should flex."""
    TIGHT = "tight"
    LOOSE = "loose"


class WrapAlignment:
    """How children within a run of a Wrap widget should be placed."""
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space_between"
    SPACE_AROUND = "space_around"
    SPACE_EVENLY = "space_evenly"


class Axis:
    """The two cardinal directions in 2D coordinate spaces."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Curves:
    """Standard animation curves."""
    LINEAR = "linear"
    EASE_IN = "easeIn"
    EASE_OUT = "easeOut"
    EASE_IN_OUT = "easeInOut"
    BOUNCE_IN = "bounceIn"
    BOUNCE_OUT = "bounceOut"
    BOUNCE_IN_OUT = "bounceInOut"
    ELASTIC_IN = "elasticIn"
    ELASTIC_OUT = "elasticOut"
    ELASTIC_IN_OUT = "elasticInOut"
    FAST_OUT_SLOW_IN = "fastOutSlowIn"


class HitTestBehavior:
    """How a gesture detector behaves during hit testing."""
    DEFER_TO_CHILD = "defer_to_child"
    OPAQUE = "opaque"
    TRANSLUCENT = "translucent"


class DismissDirection:
    """Directions in which a Dismissible widget can be dismissed."""
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    END_TO_START = "end_to_start"
    START_TO_END = "start_to_end"
    UP = "up"
    DOWN = "down"
    NONE = "none"


class Alignment:
    """Standard 2D alignments within a box."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class FloatingActionButtonLocation:
    """Standard placement locations for FloatingActionButton in a Scaffold."""
    CENTER_FLOAT = "centerFloat"
    CENTER_DOCKED = "centerDocked"
    END_FLOAT = "endFloat"
    END_DOCKED = "endDocked"
    START_FLOAT = "startFloat"
    START_DOCKED = "startDocked"


class ScrollPhysics:
    """Physics applied to scrollable views like ListView and SingleChildScrollView."""
    BOUNCING = "bouncing"
    CLAMPING = "clamping"
    NEVER = "never"
    ALWAYS = "always"

