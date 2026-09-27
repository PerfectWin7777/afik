"""
PyShop - Native E-Commerce Mobile App built with PyFlutter.
Demonstrates:
- Live network requests (FakeStoreAPI REST API)
- Reactive asynchronous state update (self.update())
- 3 distinct tabs (Store catalog, Interactive cart, Native plugins & support)
- Dynamic shopping cart state management with live badge counter and price calculation
- Side navigation Drawer with DrawerHeader
- Native Flutter package integration (url_launcher: browser, phone, email)
- Clean Pythonic Object-Oriented Component architecture
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Auto-detect framework root so script can run seamlessly from any interpreter or directory
_repo_root = Path(__file__).resolve().parents[2]
_framework_path = _repo_root / "py_framework"
if _framework_path.exists() and str(_framework_path) not in sys.path:
    sys.path.insert(0, str(_framework_path))

from pyflutter import (
    AppBar,
    BottomNavigationBar,
    BottomNavigationBarItem,
    Button,
    Card,
    Center,
    CircularProgressIndicator,
    Colors,
    Column,
    Component,
    Container,
    CrossAxisAlignment,
    Divider,
    Drawer,
    DrawerHeader,
    Expanded,
    FontWeight,
    Icon,
    IconButton,
    Icons,
    Image,
    ListView,
    MainAxisAlignment,
    Padding,
    Row,
    Scaffold,
    SingleChildScrollView,
    SizedBox,
    Text,
    Wrap,
    run,
)
from pyflutter.core.logger import logger
from pyflutter.plugins import url_launcher


@dataclass
class Product:
    """Domain model representing a product in the catalog."""
    id: int
    title: str
    price: float
    description: str
    category: str
    image: str
    rating_rate: float
    rating_count: int


@dataclass
class CartItem:
    """Represents a product and quantity in the user's cart."""
    product: Product
    quantity: int = 1


class CategoryChip(Component):
    """Filter button chip for product categories."""

    def __init__(self, label: str, selected: bool, on_select):
        super().__init__()
        self.label = label
        self.selected = selected
        self.on_select = on_select

    def build(self):
        bg = Colors.BLUE if self.selected else Colors.WHITE
        text_color = Colors.WHITE if self.selected else Colors.GREY_800
        return Container(
            Text(self.label, font_size=13, font_weight="bold" if self.selected else "normal", color=text_color),
            padding=8,
            color=bg,
            border_radius=16,
            on_click=self.on_select,
        )


class ProductCard(Component):
    """Reusable card displaying a product with image, ratings, price, and add button."""

    def __init__(self, product: Product, on_add_to_cart):
        super().__init__()
        self.product = product
        self.on_add_to_cart = on_add_to_cart

    def build(self):
        # Truncate title if too long
        display_title = self.product.title
        if len(display_title) > 42:
            display_title = display_title[:40] + "..."

        rating_text = f"★ {self.product.rating_rate} ({self.product.rating_count})"

        return Card(
            Column([
                # Product Image
                Image(
                    self.product.image,
                    height=160,
                    fit="contain",
                    border_radius=8,
                ),
                SizedBox(height=10),

                # Category badge
                Row([
                    Container(
                        Text(self.product.category.upper(), font_size=10, font_weight="bold", color=Colors.BLUE),
                        padding=4,
                        color="#E7F3FF",
                        border_radius=6,
                    ),
                    Text(rating_text, font_size=12, color=Colors.ORANGE, font_weight="bold"),
                ], main_axis_alignment="space_between"),
                SizedBox(height=6),

                # Title
                Text(display_title, font_size=14, font_weight="bold", color=Colors.DARK_GREY),
                SizedBox(height=8),

                # Price and Add Button Row
                Row([
                    Text(f"${self.product.price:.2f}", font_size=17, font_weight="bold", color=Colors.GREEN),
                    Button(
                        "Ajouter",
                        icon=Icons.ADD,
                        color=Colors.BLUE,
                        on_click=self.on_add_to_cart,
                    ),
                ], main_axis_alignment="space_between"),
            ]),
            padding=12,
            margin=8,
            elevation=2,
            border_radius=12,
        )


class CartItemRow(Component):
    """Row displaying an item in the cart with quantity controls."""

    def __init__(self, item: CartItem, on_increase, on_decrease, on_remove):
        super().__init__()
        self.item = item
        self.on_increase = on_increase
        self.on_decrease = on_decrease
        self.on_remove = on_remove

    def build(self):
        prod = self.item.product
        item_total = prod.price * self.item.quantity

        title = prod.title if len(prod.title) < 32 else prod.title[:30] + "..."

        controls = Row([
            # Decrement button
            IconButton(Icons.REMOVE, size=20, color=Colors.GREY_700, on_click=self.on_decrease),
            Text(f"{self.item.quantity}", font_size=15, font_weight="bold"),
            # Increment button
            IconButton(Icons.ADD, size=20, color=Colors.BLUE, on_click=self.on_increase),
            SizedBox(width=8),
            # Delete button
            IconButton(Icons.DELETE_OUTLINE, size=22, color=Colors.RED, on_click=self.on_remove),
        ])

        return Card(
            Row([
                # Thumbnail
                Image(prod.image, width=60, height=60, fit="contain", border_radius=8),
                SizedBox(width=12),
                # Details
                Column([
                    Text(title, font_size=13, font_weight="bold", color=Colors.DARK_GREY),
                    SizedBox(height=4),
                    Text(f"${prod.price:.2f} × {self.item.quantity} = ${item_total:.2f}",
                         font_size=13, color=Colors.GREEN, font_weight="bold"),
                    SizedBox(height=4),
                    controls,
                ], cross_axis_alignment="start"),
            ], main_axis_alignment="start"),
            padding=10,
            margin=6,
            elevation=1,
            border_radius=10,
        )


class PyShopApp(Component):
    """Main application component managing tabs, live network fetch, and cart state."""

    def __init__(self):
        super().__init__()
        self.current_tab = 0
        self.selected_category = "Tous"
        self.products: list[Product] = []
        self.cart: list[CartItem] = []
        self.is_loading = True
        self.error_message: Optional[str] = None

        # Start live background network request
        self.fetch_products()

    def fetch_products(self):
        """Asynchronously fetches products from FakeStoreAPI."""
        self.is_loading = True
        self.error_message = None

        def worker():
            url = "https://fakestoreapi.com/products"
            logger.info(f"🌐 Fetching live catalog from {url}...")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "PyFlutter/0.1.0"})
                with urllib.request.urlopen(req, timeout=12) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    loaded = []
                    for item in data:
                        rating = item.get("rating", {})
                        prod = Product(
                            id=item["id"],
                            title=item["title"],
                            price=float(item["price"]),
                            description=item["description"],
                            category=item["category"],
                            image=item["image"],
                            rating_rate=float(rating.get("rate", 4.0)),
                            rating_count=int(rating.get("count", 0)),
                        )
                        loaded.append(prod)
                    self.products = loaded
                    self.is_loading = False
                    logger.success(f"✅ Loaded {len(loaded)} products from FakeStoreAPI!")
            except Exception as e:
                logger.error(f"Failed to fetch products: {e}")
                self.error_message = str(e)
                self.is_loading = False

            # Notify PyFlutter to re-render the UI on the phone immediately!
            self.update()

        threading.Thread(target=worker, daemon=True).start()

    # --- Cart Management ---

    def add_to_cart(self, product: Product):
        for item in self.cart:
            if item.product.id == product.id:
                item.quantity += 1
                logger.info(f"Incremented {product.title} to {item.quantity}")
                self.update()
                return
        self.cart.append(CartItem(product=product, quantity=1))
        logger.info(f"Added new product to cart: {product.title}")
        self.update()

    def increase_quantity(self, item: CartItem):
        item.quantity += 1
        self.update()

    def decrease_quantity(self, item: CartItem):
        if item.quantity > 1:
            item.quantity -= 1
        else:
            self.cart.remove(item)
        self.update()

    def remove_from_cart(self, item: CartItem):
        if item in self.cart:
            self.cart.remove(item)
            self.update()

    def clear_cart(self):
        self.cart.clear()
        self.update()

    def on_tab_selected(self, index: int):
        self.current_tab = index
        logger.info(f"Tab switched to: {index}")
        self.update()

    def set_category(self, cat: str):
        self.selected_category = cat
        self.update()

    # --- Views Builders ---

    def build_store_tab(self):
        """Tab 1: Product catalog with category filter chips."""
        if self.is_loading:
            return Center(
                Column([
                    CircularProgressIndicator(),
                    SizedBox(height=16),
                    Text("Chargement du catalogue en direct...", font_size=15, color=Colors.GREY_700),
                    SizedBox(height=8),
                    Text("FakeStoreAPI REST Client", font_size=12, color=Colors.GREY_500),
                ], main_axis_alignment="center")
            )

        if self.error_message:
            return Center(
                Column([
                    Icon(Icons.ERROR_OUTLINE, size=48, color=Colors.RED),
                    SizedBox(height=12),
                    Text("Erreur de connexion", font_size=16, font_weight="bold"),
                    SizedBox(height=6),
                    Text(self.error_message, font_size=12, color=Colors.GREY_600),
                    SizedBox(height=16),
                    Button("Réessayer", icon=Icons.REFRESH, on_click=self.fetch_products),
                ], main_axis_alignment="center")
            )

        # Categories filter bar
        categories = ["Tous", "electronics", "jewelery", "men's clothing", "women's clothing"]
        chips = [
            CategoryChip(
                label=cat.capitalize(),
                selected=(self.selected_category == cat),
                on_select=lambda target=cat: self.set_category(target),
            )
            for cat in categories
        ]
        chips_row = Padding(
            Row(chips, main_axis_alignment="space_between"),
            horizontal=8,
            vertical=6,
        )

        # Filtered products
        filtered = [
            p for p in self.products
            if self.selected_category == "Tous" or p.category.lower() == self.selected_category.lower()
        ]

        product_cards = [
            ProductCard(
                product=prod,
                on_add_to_cart=lambda target=prod: self.add_to_cart(target),
            )
            for prod in filtered
        ]

        return ListView([chips_row, *product_cards], padding=6)

    def build_cart_tab(self):
        """Tab 2: Interactive cart with total calculation and checkout."""
        if not self.cart:
            return Center(
                Column([
                    Icon(Icons.SHOPPING_CART_OUTLINED, size=64, color=Colors.GREY_400),
                    SizedBox(height=16),
                    Text("Votre panier est vide", font_size=18, font_weight="bold", color=Colors.DARK_GREY),
                    SizedBox(height=8),
                    Text("Découvrez nos produits dans l'onglet Boutique !", font_size=14, color=Colors.GREY_600),
                    SizedBox(height=20),
                    Button(
                        "Explorer la boutique",
                        icon=Icons.STORE,
                        color=Colors.BLUE,
                        on_click=lambda: self.on_tab_selected(0),
                    ),
                ], main_axis_alignment="center")
            )

        total_price = sum(item.product.price * item.quantity for item in self.cart)
        total_items = sum(item.quantity for item in self.cart)

        cart_rows = [
            CartItemRow(
                item=item,
                on_increase=lambda target=item: self.increase_quantity(target),
                on_decrease=lambda target=item: self.decrease_quantity(target),
                on_remove=lambda target=item: self.remove_from_cart(target),
            )
            for item in self.cart
        ]

        summary_card = Card(
            Column([
                Text("Récapitulatif de commande", font_size=16, font_weight="bold", color=Colors.DARK_GREY),
                Divider(height=12),
                Row([
                    Text(f"Articles ({total_items}):", font_size=14, color=Colors.GREY_700),
                    Text(f"${total_price:.2f}", font_size=14, font_weight="bold"),
                ], main_axis_alignment="space_between"),
                SizedBox(height=6),
                Row([
                    Text("Livraison:", font_size=14, color=Colors.GREY_700),
                    Text("GRATUITE", font_size=14, font_weight="bold", color=Colors.GREEN),
                ], main_axis_alignment="space_between"),
                Divider(height=16),
                Row([
                    Text("Total TTC:", font_size=17, font_weight="bold"),
                    Text(f"${total_price:.2f}", font_size=19, font_weight="bold", color=Colors.GREEN),
                ], main_axis_alignment="space_between"),
                SizedBox(height=14),
                Button(
                    f"Passer la commande (${total_price:.2f})",
                    icon=Icons.PAYMENT,
                    color=Colors.GREEN,
                    on_click=self.clear_cart,
                ),
            ]),
            padding=14,
            margin=8,
            elevation=3,
            border_radius=12,
        )

        return ListView([*cart_rows, summary_card], padding=6)

    def build_support_tab(self):
        """Tab 3: Native packages & Support showcase using url_launcher."""
        card_api = Card(
            Column([
                Row([
                    Icon(Icons.PUBLIC, size=24, color=Colors.BLUE),
                    SizedBox(width=10),
                    Text("API Live FakeStoreAPI", font_size=16, font_weight="bold"),
                ]),
                SizedBox(height=8),
                Text(
                    "Cette application interroge en direct le serveur REST https://fakestoreapi.com/products.\n"
                    "Les requêtes sont exécutées par Python et le rendu est assuré par Flutter.",
                    font_size=13,
                    color=Colors.GREY_700,
                ),
                SizedBox(height=12),
                Button(
                    "Ouvrir la documentation API",
                    icon=Icons.OPEN_IN_NEW,
                    color=Colors.BLUE,
                    on_click=lambda: url_launcher.open_url("https://fakestoreapi.com"),
                ),
            ]),
            padding=14,
            margin=8,
            elevation=2,
            border_radius=12,
        )

        card_native = Card(
            Column([
                Row([
                    Icon(Icons.SMARTPHONE, size=24, color=Colors.PURPLE),
                    SizedBox(width=10),
                    Text("Package Natif : url_launcher", font_size=16, font_weight="bold"),
                ]),
                SizedBox(height=8),
                Text(
                    "Démontre l'intégration réelle de packages Flutter pilotés depuis Python.\n"
                    "Cliquez pour déclencher le composeur d'appel ou l'application e-mail de votre téléphone :",
                    font_size=13,
                    color=Colors.GREY_700,
                ),
                SizedBox(height=12),
                Wrap([
                    Button(
                        "Appeler Support",
                        icon=Icons.PHONE,
                        color=Colors.GREEN,
                        on_click=lambda: url_launcher.make_call("+33123456789"),
                    ),
                    Button(
                        "Envoyer Email",
                        icon=Icons.EMAIL,
                        color=Colors.DEEP_PURPLE,
                        on_click=lambda: url_launcher.send_email(
                            "support@pyshop.dev",
                            subject="Question sur ma commande PyShop",
                        ),
                    ),
                ], spacing=10, run_spacing=10),
            ]),
            padding=14,
            margin=8,
            elevation=2,
            border_radius=12,
        )

        card_specs = Card(
            Column([
                Row([
                    Icon(Icons.CHECK_CIRCLE, size=24, color=Colors.GREEN),
                    SizedBox(width=10),
                    Text("Performances & Architecture", font_size=16, font_weight="bold"),
                ]),
                SizedBox(height=8),
                Text("• Moteur graphique : Flutter Engine (GPU Skia/Impeller)", font_size=13),
                SizedBox(height=4),
                Text("• Pont haute vitesse : Rust Protobuf Binary Relay", font_size=13),
                SizedBox(height=4),
                Text("• Logique métier & État : Python 3.12 POO", font_size=13),
                SizedBox(height=4),
                Text("• Fréquence d'affichage : 60 FPS constant", font_size=13),
            ]),
            padding=14,
            margin=8,
            elevation=2,
            border_radius=12,
        )

        return ListView([card_api, card_native, card_specs], padding=6)

    def build_drawer(self):
        """Constructs the slide-out navigation drawer."""
        header = DrawerHeader(
            Column([
                Row([
                    Icon(Icons.STOREFRONT, size=32, color=Colors.WHITE),
                    SizedBox(width=10),
                    Text("PyShop Mobile", font_size=20, font_weight="bold", color=Colors.WHITE),
                ]),
                SizedBox(height=6),
                Text("Tony Dev • Compte VIP", font_size=13, color="#D0E3FF"),
            ], main_axis_alignment="center", cross_axis_alignment="start"),
            background_color=Colors.BLUE,
        )

        items = [
            Container(
                Row([
                    Icon(Icons.STORE, color=Colors.BLUE, size=22),
                    SizedBox(width=12),
                    Text("Boutique en ligne", font_size=15, font_weight="bold"),
                ]),
                padding=12,
                on_click=lambda: self.on_tab_selected(0),
            ),
            Container(
                Row([
                    Icon(Icons.SHOPPING_CART, color=Colors.GREEN, size=22),
                    SizedBox(width=12),
                    Text(f"Mon Panier ({len(self.cart)})", font_size=15, font_weight="bold"),
                ]),
                padding=12,
                on_click=lambda: self.on_tab_selected(1),
            ),
            Container(
                Row([
                    Icon(Icons.INFO, color=Colors.PURPLE, size=22),
                    SizedBox(width=12),
                    Text("Plugins & Support", font_size=15, font_weight="bold"),
                ]),
                padding=12,
                on_click=lambda: self.on_tab_selected(2),
            ),
            Divider(height=16),
            Container(
                Row([
                    Icon(Icons.REFRESH, color=Colors.GREY_700, size=22),
                    SizedBox(width=12),
                    Text("Actualiser le catalogue", font_size=14),
                ]),
                padding=12,
                on_click=self.fetch_products,
            ),
        ]

        return Drawer(
            Column([header, *items], cross_axis_alignment="stretch"),
            background_color=Colors.WHITE,
        )

    def build(self):
        cart_badge = f" ({len(self.cart)})" if self.cart else ""

        # AppBar
        app_bar = AppBar(
            title=Text("PyShop", font_size=20, font_weight="bold", color=Colors.WHITE),
            background_color=Colors.BLUE,
            elevation=2,
            actions=[
                Container(
                    Icon(Icons.REFRESH, color=Colors.WHITE, size=22),
                    padding=8,
                    on_click=self.fetch_products,
                ),
                Container(
                    Row([
                        Icon(Icons.SHOPPING_CART, color=Colors.WHITE, size=22),
                        Text(f" {len(self.cart)}", font_size=14, font_weight="bold", color=Colors.WHITE),
                    ]),
                    padding=8,
                    on_click=lambda: self.on_tab_selected(1),
                ),
            ],
        )

        # Body according to selected tab
        if self.current_tab == 0:
            body_content = self.build_store_tab()
        elif self.current_tab == 1:
            body_content = self.build_cart_tab()
        else:
            body_content = self.build_support_tab()

        # Bottom navigation bar
        nav_bar = BottomNavigationBar(
            items=[
                BottomNavigationBarItem(Icons.STORE, "Boutique"),
                BottomNavigationBarItem(Icons.SHOPPING_CART, f"Panier{cart_badge}"),
                BottomNavigationBarItem(Icons.HELP_OUTLINE, "Support"),
            ],
            current_index=self.current_tab,
            selected_color=Colors.BLUE,
            unselected_color=Colors.GREY,
            on_tap=self.on_tab_selected,
        )

        return Scaffold(
            app_bar=app_bar,
            drawer=self.build_drawer(),
            body=body_content,
            bottom_navigation_bar=nav_bar,
            background_color=Colors.LIGHT_GREY,
        )


if __name__ == "__main__":
    run(PyShopApp())
