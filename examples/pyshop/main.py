"""
PyShop — Modern E-Commerce Application built with Afik.

Demonstrates:
- Clean PyQt/PySide-style Object-Oriented Component Architecture
  (imperative layout assembly via add_widget(), add_spacing(), add_divider(), QtSignals)
- Material 3 Design System with dynamic ColorScheme seed & Typography scale
- Native Widgets: Badge, Chip, ListTile, Slider, FloatingActionButton, Card, TextField
- Live search query and interactive price filter slider
- Reactive shopping cart with live item counter badge and total calculation
- Native overlays: SnackBar with action callback, Material 3 AlertDialog
- Native mobile integrations via url_launcher (external browser, phone dialer, email)
"""

from __future__ import annotations

import json
import threading
import urllib.request
from dataclasses import dataclass
from typing import Optional

from afik import (
    Alignment,
    AppBar,
    Axis,
    Badge,
    BottomNavigationBar,
    BottomNavigationBarItem,
    BoxFit,
    BoxShape,
    Button,
    Card,
    Center,
    Chip,
    CircularProgressIndicator,
    ColorScheme,
    Colors,
    Column,
    Component,
    Container,
    CrossAxisAlignment,
    Divider,
    Drawer,
    DrawerHeader,
    Duration,
    ElevatedButton,
    Expanded,
    FloatingActionButton,
    FloatingActionButtonLocation,
    FontWeight,
    Icon,
    IconButton,
    Icons,
    Image,
    InputBorder,
    ListTile,
    ListView,
    MainAxisAlignment,
    MainAxisSize,
    MainWindow,
    MaterialApp,
    OutlinedButton,
    Padding,
    Row,
    Scaffold,
    ScrollPhysics,
    SingleChildScrollView,
    SizedBox,
    Slider,
    Text,
    TextButton,
    TextEditingController,
    TextField,
    TextOverflow,
    ThemeData,
    ThemeMode,
    VerticalDivider,
    Widget,
    Wrap,
    run,
    show_dialog,
    show_snack_bar,
)
from afik.core.logger import logger
from afik.plugins import url_launcher


# ==============================================================================
# Domain Models
# ==============================================================================

@dataclass
class Product:
    """Domain model representing a retail product in the catalog."""
    id: int
    title: str
    price: float
    category: str
    rating: float
    reviews_count: int
    image: str
    description: str


@dataclass
class CartItem:
    """Domain model representing an item in the user's shopping cart."""
    product: Product
    quantity: int = 1

    @property
    def total_price(self) -> float:
        return self.product.price * self.quantity


# ==============================================================================
# Curated Tech Catalog (Offline Fallback & Instant Render)
# ==============================================================================

CURATED_CATALOG: list[Product] = [
    Product(
        id=1,
        title="MacBook Pro 16\" M3 Max",
        category="Laptops",
        price=2499.00,
        rating=4.9,
        reviews_count=328,
        image="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=60",
        description="Apple M3 Max chip with 16-core CPU, 40-core GPU, 48GB unified memory, and 1TB SSD storage.",
    ),
    Product(
        id=2,
        title="Sony WH-1000XM5 Wireless Headphones",
        category="Audio",
        price=398.00,
        rating=4.8,
        reviews_count=512,
        image="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60",
        description="Industry-leading noise canceling with dual processors, 8 microphones, and 30-hour battery life.",
    ),
    Product(
        id=3,
        title="Apple Watch Ultra 2 GPS + Cellular",
        category="Wearables",
        price=799.00,
        rating=4.9,
        reviews_count=184,
        image="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60",
        description="Rugged 49mm titanium case, precision dual-frequency GPS, and 3000 nits brightest display.",
    ),
    Product(
        id=4,
        title="Dell UltraSharp 32\" 4K USB-C Hub Monitor",
        category="Displays",
        price=689.50,
        rating=4.7,
        reviews_count=96,
        image="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=60",
        description="IPS Black technology with 2000:1 contrast ratio, 4K UHD clarity, and 90W laptop power delivery.",
    ),
    Product(
        id=5,
        title="Keychron Q1 Pro Wireless Mechanical Keyboard",
        category="Accessories",
        price=199.00,
        rating=4.8,
        reviews_count=410,
        image="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60",
        description="Full aluminum CNC machined body, hot-swappable switches, QMK/VIA programmable, RGB backlight.",
    ),
    Product(
        id=6,
        title="Logitech MX Master 3S Performance Mouse",
        category="Accessories",
        price=99.99,
        rating=4.9,
        reviews_count=874,
        image="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60",
        description="8K DPI any-surface glass tracking, quiet clicks, MagSpeed electromagnetic wheel, USB-C fast charging.",
    ),
    Product(
        id=7,
        title="iPad Pro 13\" M4 Ultra Retina OLED",
        category="Tablets",
        price=1299.00,
        rating=4.9,
        reviews_count=142,
        image="https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&auto=format&fit=crop&q=60",
        description="Breakthrough Tandem OLED display, M4 neural chip performance, and ultra-thin aluminum chassis.",
    ),
    Product(
        id=8,
        title="Bose QuietComfort Ultra Earbuds",
        category="Audio",
        price=299.00,
        rating=4.6,
        reviews_count=215,
        image="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=60",
        description="Spatial audio with CustomTune calibration, world-class active noise cancellation, and touch controls.",
    ),
]


# ==============================================================================
# Subcomponents (PyQt / PySide OOP Style)
# ==============================================================================

class ProductCard(Component):
    """
    Card displaying a single product in the catalog.
    Assembled imperatively in PyQt style with add_widget(), add_spacing(), and QtSignals.
    """

    def __init__(self, product: Product, on_add_to_cart):
        super().__init__()
        self.product = product
        self.on_add_to_cart = on_add_to_cart

    def build(self) -> Card:
        # 1. Product Image
        img = Image(
            self.product.image,
            height=160,
            fit=BoxFit.COVER,
            border_radius=10,
        )

        # 2. Category badge & Rating star row
        meta_row = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        cat_badge = Container(
            Text(
                self.product.category.upper(),
                font_size=10,
                font_weight=FontWeight.BOLD,
                color=Colors.NAVY,
            ),
            padding=4,
            color=Colors.BLUE_100,
            border_radius=6,
        )
        rating_box = Row(main_axis_size=MainAxisSize.MIN)
        rating_box.add_widget(Icon(Icons.STAR, size=15, color=Colors.AMBER_500))
        rating_box.add_spacing(4)
        rating_box.add_widget(
            Text(
                f"{self.product.rating:.1f} ({self.product.reviews_count})",
                font_size=12,
                font_weight=FontWeight.BOLD,
                color=Colors.SLATE_600,
            )
        )
        meta_row.add_widget(cat_badge).add_widget(rating_box)

        # 3. Title & Description
        title_text = Text(
            self.product.title,
            font_size=15,
            font_weight=FontWeight.BOLD,
            color=Colors.SLATE_900,
            max_lines=1,
            overflow=TextOverflow.ELLIPSIS,
        )
        desc_text = Text(
            self.product.description,
            font_size=12,
            color=Colors.SLATE_500,
            max_lines=2,
            overflow=TextOverflow.ELLIPSIS,
        )

        # 4. Price & Action button row
        action_row = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        price_text = Text(
            f"${self.product.price:,.2f}",
            font_size=18,
            font_weight=FontWeight.BOLD,
            color=Colors.EMERALD_600,
        )
        add_btn = Button(
            "Add to Cart",
            icon=Icons.ADD_SHOPPING_CART,
            background_color=Colors.NAVY,
            color=Colors.WHITE,
            border_radius=8.0,
            elevation=2.0,
        )
        add_btn.clicked.connect(lambda: self.on_add_to_cart(self.product))
        action_row.add_widget(price_text).add_widget(add_btn)

        # 5. Assemble Card body in pure imperative PyQt style
        layout = Column()
        layout.add_widget(img)
        layout.add_spacing(10)
        layout.add_widget(meta_row)
        layout.add_spacing(8)
        layout.add_widget(title_text)
        layout.add_spacing(4)
        layout.add_widget(desc_text)
        layout.add_spacing(12)
        layout.add_widget(action_row)

        return Card(
            layout,
            padding=12,
            margin=8,
            elevation=1.5,
            border_radius=14,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
            raw_props={"key": f"product_card_{self.product.id}"},
        )


class CartItemRow(Component):
    """
    Card displaying an item in the cart with quantity steppers and delete action.
    """

    def __init__(self, item: CartItem, on_increase, on_decrease, on_remove):
        super().__init__()
        self.item = item
        self.on_increase = on_increase
        self.on_decrease = on_decrease
        self.on_remove = on_remove

    def build(self) -> Card:
        prod = self.item.product

        # 1. Product Image Thumbnail
        thumb = Image(
            prod.image,
            width=70,
            height=70,
            fit=BoxFit.COVER,
            border_radius=8,
        )

        # 2. Right details & controls column
        right_col = Column(cross_axis_alignment=CrossAxisAlignment.START)

        # Top line: Title (takes all available width with ellipsis) + Delete button
        top_line = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        title_text = Text(
            prod.title,
            font_size=14,
            font_weight=FontWeight.BOLD,
            color=Colors.SLATE_900,
            max_lines=1,
            overflow=TextOverflow.ELLIPSIS,
        )
        del_btn = IconButton(
            Icons.DELETE_OUTLINE,
            size=18,
            color=Colors.RED_600,
            padding=2,
            on_pressed=lambda: self.on_remove(self.item),
        )
        top_line.add_widget(Expanded(title_text))
        top_line.add_widget(del_btn)
        right_col.add_widget(top_line)

        # Unit price
        right_col.add_widget(
            Text(
                f"${prod.price:,.2f} each",
                font_size=12,
                color=Colors.SLATE_500,
            )
        )
        right_col.add_spacing(4)

        # Bottom line: Subtotal + Stepper controls
        bottom_line = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        subtotal_text = Text(
            f"Total: ${self.item.total_price:,.2f}",
            font_size=13,
            font_weight=FontWeight.BOLD,
            color=Colors.EMERALD_600,
        )
        bottom_line.add_widget(subtotal_text)

        steppers = Row(main_axis_size=MainAxisSize.MIN, cross_axis_alignment=CrossAxisAlignment.CENTER)
        minus_btn = IconButton(
            Icons.REMOVE,
            size=16,
            color=Colors.SLATE_600,
            padding=2,
            on_pressed=lambda: self.on_decrease(self.item),
        )
        qty_badge = Container(
            Text(
                str(self.item.quantity),
                font_size=13,
                font_weight=FontWeight.BOLD,
                color=Colors.SLATE_900,
            ),
            padding=4,
            color=Colors.SLATE_100,
            border_radius=4,
        )
        plus_btn = IconButton(
            Icons.ADD,
            size=16,
            color=Colors.NAVY,
            padding=2,
            on_pressed=lambda: self.on_increase(self.item),
        )
        steppers.add_widget(minus_btn)
        steppers.add_spacing(2)
        steppers.add_widget(qty_badge)
        steppers.add_spacing(2)
        steppers.add_widget(plus_btn)

        bottom_line.add_widget(steppers)
        right_col.add_widget(bottom_line)

        # Assemble main card row
        card_row = Row(cross_axis_alignment=CrossAxisAlignment.CENTER)
        card_row.add_widget(thumb)
        card_row.add_spacing(10)
        card_row.add_widget(Expanded(right_col))

        return Card(
            card_row,
            padding=10,
            margin=6,
            elevation=1.0,
            border_radius=10,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
            raw_props={"key": f"cart_item_{self.item.product.id}"},
        )


# ==============================================================================
# Main Application Window (MainWindow / Component)
# ==============================================================================

class PyShopWindow(MainWindow):
    """
    Main application shell managing navigation tabs, live catalog filtering,
    dynamic shopping cart state, and native system integrations.
    """

    def __init__(self):
        super().__init__()
        self.current_tab: int = 0
        self.selected_category: str = "All"
        self.search_query: str = ""
        self.max_price: float = 3000.0

        self.products: list[Product] = list(CURATED_CATALOG)
        self.cart: list[CartItem] = [
            CartItem(product=CURATED_CATALOG[0], quantity=1),  # MacBook Pro
            CartItem(product=CURATED_CATALOG[1], quantity=1),  # Sony Headphones
        ]
        self.is_loading: bool = False
        self.categories: list[str] = ["All", "Laptops", "Audio", "Wearables", "Displays", "Accessories", "Tablets"]

        # Search field controller
        self.search_controller = TextEditingController(text="")

        # Start background sync to fetch extra items from FakeStoreAPI
        self.sync_remote_catalog()

    # --------------------------------------------------------------------------
    # Catalog Networking & Sync
    # --------------------------------------------------------------------------

    def sync_remote_catalog(self) -> None:
        """Asynchronously queries FakeStoreAPI in a background thread."""
        def worker():
            url = "https://fakestoreapi.com/products"
            logger.info(f"🌐 Synchronizing catalog with remote API {url}...")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Afik/0.1.0"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    new_items = []
                    for item in data[:6]:  # Import top 6 items
                        rating_dict = item.get("rating", {})
                        new_items.append(
                            Product(
                                id=100 + int(item["id"]),
                                title=str(item["title"]),
                                price=float(item["price"]),
                                category="General",
                                rating=float(rating_dict.get("rate", 4.5)),
                                reviews_count=int(rating_dict.get("count", 40)),
                                image=str(item["image"]),
                                description=str(item["description"]),
                            )
                        )
                    # Merge unique remote products
                    existing_ids = {p.id for p in self.products}
                    for item in new_items:
                        if item.id not in existing_ids:
                            self.products.append(item)
                    logger.success(f"✅ Catalog synchronized! {len(self.products)} total products available.")
                    self.update()
            except Exception as e:
                logger.warning(f"Remote catalog sync skipped ({e}). Working smoothly in offline mode.")

        threading.Thread(target=worker, daemon=True).start()

    # --------------------------------------------------------------------------
    # Cart State Management & Signals
    # --------------------------------------------------------------------------

    def add_to_cart(self, product: Product) -> None:
        """Adds a product to the cart or increments its quantity."""
        for item in self.cart:
            if item.product.id == product.id:
                item.quantity += 1
                logger.info(f"Incremented quantity for {product.title}: {item.quantity}")
                self.update()
                show_snack_bar(
                    f"Added another {product.title} to bag",
                    duration=Duration(seconds=3),
                    action="VIEW BAG",
                    on_action=lambda: self.switch_tab(1),
                )
                return

        self.cart.append(CartItem(product=product, quantity=1))
        logger.info(f"Added new item to cart: {product.title}")
        self.update()

        # Native floating feedback
        show_snack_bar(
            f"Added {product.title} to bag",
            duration=Duration(seconds=3),
            action="VIEW BAG",
            on_action=lambda: self.switch_tab(1),
        )

    def increase_quantity(self, item: CartItem) -> None:
        item.quantity += 1
        self.update()

    def decrease_quantity(self, item: CartItem) -> None:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            self.cart.remove(item)
        self.update()

    def remove_from_cart(self, item: CartItem) -> None:
        if item in self.cart:
            self.cart.remove(item)
            self.update()
            show_snack_bar("Item removed from your cart", duration=Duration(seconds=2))

    def clear_cart(self) -> None:
        self.cart.clear()
        self.update()

    def switch_tab(self, index: int) -> None:
        self.current_tab = index
        self.update()

    @property
    def cart_count(self) -> int:
        return sum(item.quantity for item in self.cart)

    @property
    def cart_total(self) -> float:
        return sum(item.total_price for item in self.cart)

    # --------------------------------------------------------------------------
    # Interactive Event Handlers
    # --------------------------------------------------------------------------

    def _on_search_changed(self, query: str) -> None:
        self.search_query = query.strip()
        self.update()

    def _on_price_changed(self, new_val: float) -> None:
        self.max_price = round(float(new_val), 0)
        self.update()

    def _on_category_selected(self, cat: str) -> None:
        self.selected_category = cat
        self.update()

    def _trigger_checkout_dialog(self) -> None:
        """Presents a Material 3 alert dialog confirming the transaction."""
        total = self.cart_total
        count = self.cart_count

        def handle_confirm():
            self.clear_cart()
            show_snack_bar(
                "🎉 Order placed successfully! Receipt sent to your email.",
                duration=Duration(seconds=5),
            )

        show_dialog(
            title="Confirm Order",
            content=f"Proceed with checkout for {count} items?\nTotal amount: ${total:,.2f} (Tax Included)",
            confirm_label="Confirm & Pay",
            cancel_label="Review Bag",
            on_confirm=handle_confirm,
        )

    # --------------------------------------------------------------------------
    # View Builders (Catalog, Cart, Account/Support)
    # --------------------------------------------------------------------------

    def build_store_tab(self) -> Widget:
        """Tab 0: Store catalog with search bar, category chips, and price slider."""
        items: list[Widget] = []

        # 1. Search Bar
        search_field = TextField(
            value=self.search_query,
            controller=self.search_controller,
            placeholder="Search products, brands, accessories...",
            prefix_icon=Icons.SEARCH,
            suffix_icon=Icons.CLOSE if self.search_query else None,
            on_suffix_icon_click=lambda: self.search_controller.clear(),
            border=InputBorder.OUTLINE,
            border_radius=12.0,
            filled=True,
            fill_color=Colors.WHITE,
        )
        search_field.textChanged.connect(self._on_search_changed)
        search_padding = Padding(search_field, horizontal=8, vertical=4)
        items.append(search_padding)

        # 2. Filter Category Chips (Horizontally Scrollable)
        chips_list = Row()
        for cat in self.categories:
            is_active = (self.selected_category.lower() == cat.lower())
            chip = Chip(
                label=cat,
                avatar=Icons.CHECK if is_active else None,
                background_color=Colors.NAVY if is_active else Colors.WHITE,
                on_pressed=lambda c=cat: self._on_category_selected(c),
            )
            chips_list.add_widget(chip)
            chips_list.add_spacing(8)

        chips_scroll = SingleChildScrollView(
            chips_list,
            scroll_direction=Axis.HORIZONTAL,
            padding=8,
        )
        items.append(chips_scroll)

        # 3. Interactive Price Range Filter (Showcase Slider)
        price_filter_card = Card(
            padding=10,
            margin=8,
            elevation=1.0,
            border_radius=12,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
        )
        price_header = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        price_header.add_widget(
            Text(
                "Filter by Max Price",
                font_size=13,
                font_weight=FontWeight.BOLD,
                color=Colors.SLATE_600,
            )
        )
        price_header.add_widget(
            Text(
                f"${self.max_price:,.0f}",
                font_size=14,
                font_weight=FontWeight.BOLD,
                color=Colors.NAVY,
            )
        )
        price_slider = Slider(
            value=self.max_price,
            min=50.0,
            max=3000.0,
            divisions=59,
            active_color=Colors.NAVY,
            inactive_color=Colors.SLATE_300,
            label=f"${self.max_price:,.0f}",
        )
        price_slider.valueChanged.connect(self._on_price_changed)

        price_box = Column()
        price_box.add_widget(price_header)
        price_box.add_widget(price_slider)
        price_filter_card.add_widget(price_box)
        items.append(price_filter_card)

        # 4. Filter products
        filtered = [
            p for p in self.products
            if (self.selected_category == "All" or p.category.lower() == self.selected_category.lower())
            and (not self.search_query or self.search_query.lower() in p.title.lower() or self.search_query.lower() in p.description.lower())
            and p.price <= self.max_price
        ]

        # 5. Product Results Counter
        counter_row = Row(
            main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN,
            cross_axis_alignment=CrossAxisAlignment.CENTER,
        )
        counter_row.add_widget(
            Text(
                f"Showing {len(filtered)} items",
                font_size=13,
                font_weight=FontWeight.BOLD,
                color=Colors.SLATE_500,
            )
        )
        if self.selected_category != "All" or self.search_query or self.max_price < 3000:
            reset_btn = TextButton(
                "Reset Filters",
                color=Colors.RED_600,
                on_pressed=lambda: self._reset_filters(),
            )
            counter_row.add_widget(reset_btn)
        items.append(Padding(counter_row, horizontal=12, vertical=4))

        # 6. Product Cards or Empty State
        col = Column()
        col.add_widget(search_padding)
        col.add_widget(chips_scroll)
        col.add_widget(price_filter_card)
        col.add_widget(Padding(counter_row, horizontal=12, vertical=4))

        if not filtered:
            col.add_widget(empty_box)
        else:
            for prod in filtered:
                col.add_widget(ProductCard(prod, on_add_to_cart=self.add_to_cart))

        return SingleChildScrollView(
            col,
            padding=6,
            physics=ScrollPhysics.BOUNCING,
            raw_props={"key": "store_scroll_view"},
        )

    def _reset_filters(self) -> None:
        self.selected_category = "All"
        self.search_query = ""
        self.max_price = 3000.0
        self.search_controller.clear()
        self.update()

    def build_cart_tab(self) -> Widget:
        """Tab 1: Shopping cart with live item management, subtotal, and checkout."""
        if not self.cart:
            empty_layout = Column(main_axis_alignment=MainAxisAlignment.CENTER)
            empty_layout.add_widget(Icon(Icons.SHOPPING_BAG_OUTLINED, size=72, color=Colors.SLATE_400))
            empty_layout.add_spacing(16)
            empty_layout.add_widget(
                Text(
                    "Your Shopping Bag is Empty",
                    font_size=19,
                    font_weight=FontWeight.BOLD,
                    color=Colors.SLATE_900,
                )
            )
            empty_layout.add_spacing(8)
            empty_layout.add_widget(
                Text(
                    "Explore the catalog to discover cutting-edge tech gear.",
                    font_size=14,
                    color=Colors.SLATE_500,
                )
            )
            empty_layout.add_spacing(20)
            explore_btn = Button(
                "Explore Catalog",
                icon=Icons.STOREFRONT,
                background_color=Colors.NAVY,
                color=Colors.WHITE,
                border_radius=8.0,
                elevation=2.0,
            )
            explore_btn.clicked.connect(lambda: self.switch_tab(0))
            empty_layout.add_widget(explore_btn)
            return Center(empty_layout)

        total_price = self.cart_total
        total_items = self.cart_count

        items: list[Widget] = []
        for item in self.cart:
            items.append(
                CartItemRow(
                    item=item,
                    on_increase=self.increase_quantity,
                    on_decrease=self.decrease_quantity,
                    on_remove=self.remove_from_cart,
                )
            )

        # Order Summary Card
        summary_card = Card(
            padding=16,
            margin=8,
            elevation=2.0,
            border_radius=14,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
        )
        summary_layout = Column()
        summary_layout.add_widget(
            Text(
                "Order Summary",
                font_size=17,
                font_weight=FontWeight.BOLD,
                color=Colors.SLATE_900,
            )
        )
        summary_layout.add_divider(height=16, thickness=1.0)

        # Subtotal row
        subtotal_row = Row(main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)
        subtotal_row.add_widget(Text(f"Items ({total_items}):", font_size=14, color=Colors.SLATE_500))
        subtotal_row.add_widget(Text(f"${total_price:,.2f}", font_size=14, font_weight=FontWeight.BOLD))
        summary_layout.add_widget(subtotal_row)
        summary_layout.add_spacing(6)

        # Delivery row
        delivery_row = Row(main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)
        delivery_row.add_widget(Text("Express Shipping:", font_size=14, color=Colors.SLATE_500))
        delivery_row.add_widget(
            Text("FREE", font_size=14, font_weight=FontWeight.BOLD, color=Colors.EMERALD_600)
        )
        summary_layout.add_widget(delivery_row)
        summary_layout.add_spacing(6)

        # Estimated Tax row
        tax_row = Row(main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)
        tax_row.add_widget(Text("Estimated Taxes:", font_size=14, color=Colors.SLATE_500))
        tax_row.add_widget(Text("Included", font_size=14, color=Colors.SLATE_500))
        summary_layout.add_widget(tax_row)
        summary_layout.add_divider(height=18, thickness=1.0)

        # Grand Total row
        total_row = Row(main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)
        total_row.add_widget(Text("Grand Total:", font_size=17, font_weight=FontWeight.BOLD, color=Colors.SLATE_900))
        total_row.add_widget(
            Text(
                f"${total_price:,.2f}",
                font_size=20,
                font_weight=FontWeight.BOLD,
                color=Colors.EMERALD_600,
            )
        )
        summary_layout.add_widget(total_row)
        summary_layout.add_spacing(16)

        # Checkout Button
        checkout_btn = Button(
            f"Proceed to Checkout (${total_price:,.2f})",
            icon=Icons.LOCK,
            background_color=Colors.EMERALD_600,
            color=Colors.WHITE,
            border_radius=10.0,
            elevation=3.0,
        )
        checkout_btn.clicked.connect(self._trigger_checkout_dialog)
        summary_layout.add_widget(checkout_btn)

        summary_card.add_widget(summary_layout)
        items.append(summary_card)

        return SingleChildScrollView(
            Column(items),
            padding=6,
            physics=ScrollPhysics.BOUNCING,
            raw_props={"key": "cart_scroll_view"},
        )

    def build_profile_tab(self) -> Widget:
        """Tab 2: User profile, settings list tiles, and native mobile plugins."""
        items: list[Widget] = []

        # 1. Profile Overview Card
        profile_card = Card(
            padding=16,
            margin=8,
            elevation=1.5,
            border_radius=14,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
        )
        p_row = Row(cross_axis_alignment=CrossAxisAlignment.CENTER)
        avatar = Container(
            Icon(Icons.PERSON, size=32, color=Colors.WHITE),
            color=Colors.NAVY,
            padding=14,
            shape=BoxShape.CIRCLE,
        )
        p_info = Column(cross_axis_alignment=CrossAxisAlignment.START)
        p_info.add_widget(Text("Tony Stark", font_size=18, font_weight=FontWeight.BOLD, color=Colors.SLATE_900))
        p_info.add_spacing(4)
        p_info.add_widget(
            Container(
                Text("VIP PLATINUM MEMBER", font_size=11, font_weight=FontWeight.BOLD, color=Colors.NAVY),
                padding=4,
                color=Colors.BLUE_100,
                border_radius=6,
            )
        )
        p_info.add_spacing(2)
        p_info.add_widget(Text("stark@avengers.org", font_size=13, color=Colors.SLATE_500))

        p_row.add_widget(avatar)
        p_row.add_spacing(16)
        p_row.add_widget(Expanded(p_info))
        profile_card.add_widget(p_row)
        items.append(profile_card)

        # 2. Account Preferences (ListTile Showcase)
        settings_card = Card(
            margin=8,
            elevation=1.0,
            border_radius=12,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
        )
        tiles_col = Column()
        tiles_col.add_widget(
            ListTile(
                title="Order History",
                subtitle="View past purchases and invoices",
                leading=Icon(Icons.RECEIPT_LONG, color=Colors.NAVY),
                trailing=Icon(Icons.CHEVRON_RIGHT, color=Colors.SLATE_400),
                on_tap=lambda: show_snack_bar("Displaying order history...", duration=Duration(seconds=2)),
            )
        )
        tiles_col.add_divider(height=1.0, indent=16.0, end_indent=16.0)
        tiles_col.add_widget(
            ListTile(
                title="Shipping Addresses",
                subtitle="2 locations saved (Home, Office)",
                leading=Icon(Icons.LOCATION_ON, color=Colors.EMERALD_600),
                trailing=Icon(Icons.CHEVRON_RIGHT, color=Colors.SLATE_400),
                on_tap=lambda: show_snack_bar("Shipping address settings", duration=Duration(seconds=2)),
            )
        )
        tiles_col.add_divider(height=1.0, indent=16.0, end_indent=16.0)
        tiles_col.add_widget(
            ListTile(
                title="Payment Methods",
                subtitle="Apple Pay & Visa ending in 4242",
                leading=Icon(Icons.CREDIT_CARD, color=Colors.AMBER_500),
                trailing=Icon(Icons.CHEVRON_RIGHT, color=Colors.SLATE_400),
                on_tap=lambda: show_snack_bar("Managing saved cards", duration=Duration(seconds=2)),
            )
        )
        settings_card.add_widget(tiles_col)
        items.append(settings_card)

        # 3. Native Flutter Mobile Plugin Integrations
        native_card = Card(
            padding=16,
            margin=8,
            elevation=1.0,
            border_radius=12,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.WHITE,
        )
        native_col = Column(cross_axis_alignment=CrossAxisAlignment.START)
        native_col.add_widget(
            Row([
                Icon(Icons.PHONE_ANDROID, size=22, color=Colors.VIOLET_600),
                SizedBox(width=8),
                Text(
                    "Native Device Integrations",
                    font_size=16,
                    font_weight=FontWeight.BOLD,
                    color=Colors.SLATE_900,
                ),
            ])
        )
        native_col.add_spacing(6)
        native_col.add_widget(
            Text(
                "Trigger real system features using Flutter's official url_launcher package directly from Python:",
                font_size=13,
                color=Colors.SLATE_500,
            )
        )
        native_col.add_spacing(12)

        buttons_wrap = Wrap(
            spacing=10,
            run_spacing=10,
            children=[
                OutlinedButton(
                    "Call Support",
                    icon=Icons.PHONE,
                    color=Colors.EMERALD_600,
                    on_click=lambda: url_launcher.make_call("+18005550199"),
                ),
                OutlinedButton(
                    "Send Email",
                    icon=Icons.EMAIL,
                    color=Colors.NAVY,
                    on_click=lambda: url_launcher.send_email(
                        "support@pyshop.io",
                        subject="Question regarding PyShop order",
                    ),
                ),
                OutlinedButton(
                    "API Docs",
                    icon=Icons.OPEN_IN_NEW,
                    color=Colors.SLATE_500,
                    on_click=lambda: url_launcher.open_url("https://fakestoreapi.com"),
                ),
            ],
        )
        native_col.add_widget(buttons_wrap)
        native_card.add_widget(native_col)
        items.append(native_card)

        # 4. Engine Architecture & Runtime Specifications
        specs_card = Card(
            padding=14,
            margin=8,
            elevation=1.0,
            border_radius=12,
            border_color=Colors.SLATE_200,
            border_width=1.0,
            color=Colors.SLATE_50,
        )
        specs_col = Column(cross_axis_alignment=CrossAxisAlignment.START)
        specs_col.add_widget(
            Text("Afik High-Performance Stack", font_size=14, font_weight=FontWeight.BOLD, color=Colors.SLATE_900)
        )
        specs_col.add_spacing(6)
        specs_col.add_widget(Text("• Rendering Engine: Flutter 3.24 Impeller GPU Pipeline (120 FPS)", font_size=12, color=Colors.SLATE_600))
        specs_col.add_spacing(3)
        specs_col.add_widget(Text("• Logic & Reactive State: Python 3.12 OOP Runtime", font_size=12, color=Colors.SLATE_600))
        specs_col.add_spacing(3)
        specs_col.add_widget(Text("• Bridge Protocol: Rust Binary Memory Relay & Protobuf IR", font_size=12, color=Colors.SLATE_600))
        specs_card.add_widget(specs_col)
        items.append(specs_card)

        return SingleChildScrollView(
            Column(items),
            padding=6,
            physics=ScrollPhysics.BOUNCING,
            raw_props={"key": "profile_scroll_view"},
        )

    # --------------------------------------------------------------------------
    # Scaffold & Navigation Drawer
    # --------------------------------------------------------------------------

    def build_drawer(self) -> Drawer:
        """Constructs the slide-out navigation drawer with Material 3 styling."""
        header = DrawerHeader(
            Column([
                Row([
                    Icon(Icons.STOREFRONT, size=32, color=Colors.WHITE),
                    SizedBox(width=10),
                    Text("PyShop Global", font_size=20, font_weight=FontWeight.BOLD, color=Colors.WHITE),
                ]),
                SizedBox(height=6),
                Text("Curated Tech • VIP Lounge", font_size=13, color=Colors.BLUE_200),
            ], main_axis_alignment=MainAxisAlignment.CENTER, cross_axis_alignment=CrossAxisAlignment.START),
            background_color=Colors.NAVY,
        )

        drawer_items = Column(cross_axis_alignment=CrossAxisAlignment.STRETCH)
        drawer_items.add_widget(header)

        drawer_items.add_widget(
            ListTile(
                title="Store Catalog",
                leading=Icon(Icons.STOREFRONT, color=Colors.NAVY),
                selected=(self.current_tab == 0),
                on_tap=lambda: self.switch_tab(0),
            )
        )
        drawer_items.add_widget(
            ListTile(
                title=f"My Bag ({self.cart_count})",
                leading=Icon(Icons.SHOPPING_BAG, color=Colors.EMERALD_600),
                selected=(self.current_tab == 1),
                on_tap=lambda: self.switch_tab(1),
            )
        )
        drawer_items.add_widget(
            ListTile(
                title="VIP Account & Support",
                leading=Icon(Icons.PERSON, color=Colors.VIOLET_600),
                selected=(self.current_tab == 2),
                on_tap=lambda: self.switch_tab(2),
            )
        )
        drawer_items.add_divider(height=16.0)
        drawer_items.add_widget(
            ListTile(
                title="Refresh Catalog",
                subtitle="Sync with remote API",
                leading=Icon(Icons.REFRESH, color=Colors.SLATE_600),
                on_tap=self.sync_remote_catalog,
            )
        )

        return Drawer(drawer_items, background_color=Colors.WHITE)

    def build_app_bar(self) -> AppBar:
        """Constructs the Material 3 Top AppBar with action badges."""
        badge_child = IconButton(
            Icons.SHOPPING_BAG_OUTLINED,
            color=Colors.WHITE,
            on_pressed=lambda: self.switch_tab(1),
        )
        cart_badge = Badge(
            badge_child,
            label=str(self.cart_count) if self.cart_count > 0 else None,
            is_small=(self.cart_count == 0),
            background_color=Colors.RED_600,
            text_color=Colors.WHITE,
        )

        return AppBar(
            title=Text("PyShop", font_size=20, font_weight=FontWeight.BOLD, color=Colors.WHITE),
            background_color=Colors.NAVY,
            elevation=2.0,
            scrolled_under_elevation=4.0,
            actions=[
                IconButton(
                    Icons.REFRESH,
                    color=Colors.WHITE,
                    on_pressed=self.sync_remote_catalog,
                ),
                cart_badge,
            ],
        )

    def build(self) -> Widget:
        """Assembles the root MaterialApp with Material 3 ThemeData."""
        # 1. Active view selection
        if self.current_tab == 0:
            active_body = self.build_store_tab()
            fab = FloatingActionButton.extended(
                f"Cart ({self.cart_count})",
                icon=Icons.SHOPPING_BAG,
                background_color=Colors.NAVY,
                foreground_color=Colors.WHITE,
                elevation=4.0,
                on_pressed=lambda: self.switch_tab(1),
            ) if self.cart_count > 0 else None
        elif self.current_tab == 1:
            active_body = self.build_cart_tab()
            fab = None
        else:
            active_body = self.build_profile_tab()
            fab = None

        # 2. Bottom Navigation Bar
        cart_label = f"Cart ({self.cart_count})" if self.cart_count > 0 else "Cart"
        bottom_nav = BottomNavigationBar(
            items=[
                BottomNavigationBarItem(Icons.STOREFRONT, "Store"),
                BottomNavigationBarItem(Icons.SHOPPING_BAG, cart_label),
                BottomNavigationBarItem(Icons.PERSON, "Account"),
            ],
            current_index=self.current_tab,
            selected_color=Colors.NAVY,
            unselected_color=Colors.SLATE_500,
            on_tap=self.switch_tab,
        )

        # 3. Main Scaffold
        scaffold = Scaffold(
            app_bar=self.build_app_bar(),
            drawer=self.build_drawer(),
            body=active_body,
            floating_action_button=fab,
            floating_action_button_location=FloatingActionButtonLocation.END_FLOAT,
            bottom_navigation_bar=bottom_nav,
            background_color=Colors.SLATE_50,
        )

        # 4. Wrap with Material 3 MaterialApp & ThemeData
        return MaterialApp(
            scaffold,
            title="PyShop",
            theme=ThemeData(
                color_scheme=ColorScheme.from_seed(Colors.NAVY),
                use_material3=True,
            ),
            theme_mode=ThemeMode.LIGHT,
            debug_show_checked_mode_banner=False,
        )


# ==============================================================================
# Application Entrypoint
# ==============================================================================

# Backward compatibility aliases for runner & testing
App = PyShopWindow
PyShopApp = PyShopWindow

if __name__ == "__main__":
    run(PyShopWindow())
