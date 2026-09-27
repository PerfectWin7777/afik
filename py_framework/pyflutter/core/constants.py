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
    Custom colors can also be passed directly as hex strings (e.g. "#1877F2").
    """
    # Special
    TRANSPARENT = "transparent"
    WHITE = "#FFFFFF"
    BLACK = "#000000"

    # Primaries & Brand
    BLUE = "#1877F2"
    FACEBOOK_BLUE = "#1877F2"
    LIGHT_BLUE = "#03A9F4"
    CYAN = "#00BCD4"
    TEAL = "#009688"
    GREEN = "#42B72A"
    LIGHT_GREEN = "#8BC34A"
    INDIGO = "#3F51B5"
    PURPLE = "#7B1FA2"
    DEEP_PURPLE = "#673AB7"
    PINK = "#E91E63"
    RED = "#E41E3F"
    AMBER = "#FFC107"
    ORANGE = "#FF9800"
    DEEP_ORANGE = "#FF5722"
    BROWN = "#795548"

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

    # Semantic Status Colors
    SUCCESS = "#42B72A"
    WARNING = "#FF9800"
    DANGER = "#E41E3F"
    ERROR = "#E41E3F"
    INFO = "#1877F2"
    SURFACE = "#FFFFFF"
    BACKGROUND = "#F0F2F5"


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
