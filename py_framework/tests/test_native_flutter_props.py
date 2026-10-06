"""
Unit tests for Native Flutter Widgets & Properties parity in PyFlutter.
Validates:
- ListTile, FloatingActionButton, Badge, Chip, ActionChip, VerticalDivider
- Column/Row main_axis_size
- Container alignment, margin, borders, shadows, shape
- Card shadows, surface_tint_color, border
- ListView & SingleChildScrollView shrink_wrap, physics, reverse
- TextField & TextFormField autofocus, autocorrect, cursor_color, max_length, prefix/suffix
- Scaffold & AppBar Material 3 properties
"""

import unittest

from pyflutter import (
    ActionChip,
    Alignment,
    AppBar,
    Badge,
    Card,
    Chip,
    Column,
    Container,
    Divider,
    FloatingActionButton,
    FloatingActionButtonLocation,
    ListTile,
    ListView,
    MainAxisSize,
    Row,
    Scaffold,
    ScrollPhysics,
    SingleChildScrollView,
    Text,
    TextField,
    VerticalDivider,
)
from pyflutter.core.widget_base import invoke_callback


class TestNativeFlutterWidgetsAndProps(unittest.TestCase):
    """Test suite covering extended native Flutter widget props and new widgets."""

    def test_column_and_row_main_axis_size(self):
        col = Column(main_axis_size=MainAxisSize.MIN)
        self.assertEqual(col.props["main_axis_size"], "min")
        ir = col.to_ir_dict()
        self.assertEqual(ir["props"]["main_axis_size"], "min")

        row = Row(main_axis_size="max")
        self.assertEqual(row.props["main_axis_size"], "max")

    def test_container_enhanced_props(self):
        box = Container(
            Text("Hello"),
            margin=16.0,
            alignment=Alignment.TOP_RIGHT,
            shape="circle",
            border_color="#FF0000",
            border_width=2.5,
            shadow_color="#000000",
            shadow_blur=8.0,
        )
        self.assertEqual(box.props["margin"], "16.0")
        self.assertEqual(box.props["alignment"], "top_right")
        self.assertEqual(box.props["shape"], "circle")
        self.assertEqual(box.props["border_color"], "#FF0000")
        self.assertEqual(box.props["border_width"], "2.5")
        self.assertEqual(box.props["shadow_color"], "#000000")
        self.assertEqual(box.props["shadow_blur"], "8.0")
        ir = box.to_ir_dict()
        self.assertEqual(ir["type"], "Container")
        self.assertEqual(ir["props"]["border_color"], "#FF0000")
        self.assertEqual(len(ir["children"]), 1)

    def test_card_enhanced_props(self):
        card = Card(
            Text("Card content"),
            shadow_color="#33000000",
            surface_tint_color="#1877F2",
            border_color="#E0E0E0",
            border_width=1.5,
        )
        self.assertEqual(card.props["shadow_color"], "#33000000")
        self.assertEqual(card.props["surface_tint_color"], "#1877F2")
        self.assertEqual(card.props["border_color"], "#E0E0E0")
        self.assertEqual(card.props["border_width"], "1.5")
        ir = card.to_ir_dict()
        self.assertEqual(ir["type"], "Card")

    def test_dividers(self):
        h_div = Divider(height=24.0, thickness=2.0, indent=16.0, end_indent=16.0)
        self.assertEqual(h_div.props["height"], "24.0")
        self.assertEqual(h_div.props["indent"], "16.0")
        self.assertEqual(h_div.props["end_indent"], "16.0")

        v_div = VerticalDivider(width=20.0, thickness=1.5, indent=8.0, end_indent=8.0)
        self.assertEqual(v_div.widget_type, "VerticalDivider")
        self.assertEqual(v_div.props["width"], "20.0")
        self.assertEqual(v_div.props["indent"], "8.0")
        ir = v_div.to_ir_dict()
        self.assertEqual(ir["type"], "VerticalDivider")

    def test_list_view_and_scroll_view_physics(self):
        lv = ListView(
            [Text("A"), Text("B")],
            shrink_wrap=True,
            reverse=True,
            physics=ScrollPhysics.BOUNCING,
        )
        self.assertEqual(lv.props["shrink_wrap"], "true")
        self.assertEqual(lv.props["reverse"], "true")
        self.assertEqual(lv.props["physics"], "bouncing")
        self.assertEqual(len(lv.children), 2)

        scv = SingleChildScrollView(
            Text("Content"),
            reverse=True,
            physics=ScrollPhysics.NEVER,
        )
        self.assertEqual(scv.props["reverse"], "true")
        self.assertEqual(scv.props["physics"], "never")

    def test_list_tile(self):
        clicked = []
        tile = ListTile(
            title="Account",
            subtitle="Manage personal information",
            leading=Text("ICON"),
            trailing=Text("CHEVRON"),
            dense=True,
            is_three_line=False,
            selected=True,
            tile_color="#F5F5F5",
            selected_tile_color="#E3F2FD",
            on_tap=lambda: clicked.append("tapped"),
        )
        self.assertEqual(tile.widget_type, "ListTile")
        self.assertEqual(tile.props["title"], "Account")
        self.assertEqual(tile.props["subtitle"], "Manage personal information")
        self.assertEqual(tile.props["dense"], "true")
        self.assertEqual(tile.props["selected"], "true")
        self.assertEqual(tile.props["tile_color"], "#F5F5F5")
        self.assertEqual(tile.props["selected_tile_color"], "#E3F2FD")

        # Slots on children
        slots = [c.props.get("slot") for c in tile.children]
        self.assertIn("leading", slots)
        self.assertIn("trailing", slots)

        # Event trigger
        invoke_callback(tile.callback_id, {})
        self.assertEqual(clicked, ["tapped"])

    def test_floating_action_button(self):
        pressed = []
        fab = FloatingActionButton(
            icon="add",
            tooltip="Add item",
            mini=True,
            elevation=6.0,
            background_color="#1877F2",
            on_pressed=lambda: pressed.append(1),
        )
        self.assertEqual(fab.widget_type, "FloatingActionButton")
        self.assertEqual(fab.props["icon"], "add")
        self.assertEqual(fab.props["mini"], "true")
        self.assertEqual(fab.props["elevation"], "6.0")

        invoke_callback(fab.callback_id, {})
        self.assertEqual(pressed, [1])

        # Extended FAB
        fab_ext = FloatingActionButton.extended(
            "Compose",
            icon="edit",
            background_color="#4CAF50",
            on_click=lambda: pressed.append(2),
        )
        self.assertEqual(fab_ext.props["label"], "Compose")
        self.assertEqual(fab_ext.props["icon"], "edit")
        invoke_callback(fab_ext.callback_id, {})
        self.assertEqual(pressed, [1, 2])

    def test_badge_and_chips(self):
        badge = Badge(
            Text("Cart"),
            label="3",
            background_color="#FF0000",
            text_color="#FFFFFF",
        )
        self.assertEqual(badge.widget_type, "Badge")
        self.assertEqual(badge.props["label"], "3")
        self.assertEqual(badge.props["background_color"], "#FF0000")
        self.assertEqual(len(badge.children), 1)

        chip_clicks = []
        chip = Chip(
            "Flutter",
            avatar="check",
            on_pressed=lambda: chip_clicks.append("chip"),
        )
        self.assertEqual(chip.widget_type, "Chip")
        self.assertEqual(chip.props["label"], "Flutter")
        self.assertEqual(chip.props["avatar"], "check")
        invoke_callback(chip.callback_id, {})
        self.assertEqual(chip_clicks, ["chip"])

        # ActionChip alias
        achip = ActionChip("Python")
        self.assertIsInstance(achip, Chip)

    def test_text_field_enhanced_props(self):
        tf = TextField(
            "Search query",
            autofocus=True,
            autocorrect=False,
            cursor_color="#1877F2",
            max_length=50,
            content_padding=12.0,
            prefix_text="https://",
            suffix_text=".com",
            text_capitalization="words",
        )
        self.assertEqual(tf.props["autofocus"], "true")
        self.assertEqual(tf.props["autocorrect"], "false")
        self.assertEqual(tf.props["cursor_color"], "#1877F2")
        self.assertEqual(tf.props["max_length"], "50")
        self.assertEqual(tf.props["content_padding"], "12.0")
        self.assertEqual(tf.props["prefix_text"], "https://")
        self.assertEqual(tf.props["suffix_text"], ".com")
        self.assertEqual(tf.props["text_capitalization"], "words")

    def test_scaffold_and_app_bar_props(self):
        app_bar = AppBar(
            "Dashboard",
            elevation=4.0,
            scrolled_under_elevation=8.0,
            shadow_color="#1A000000",
            surface_tint_color="#1877F2",
            toolbar_height=64.0,
            title_spacing=16.0,
            center_title=True,
        )
        self.assertEqual(app_bar.props["scrolled_under_elevation"], "8.0")
        self.assertEqual(app_bar.props["toolbar_height"], "64.0")
        self.assertEqual(app_bar.props["center_title"], "true")

        fab = FloatingActionButton(icon="add")
        scaffold = Scaffold(
            app_bar=app_bar,
            body=Text("Body"),
            floating_action_button=fab,
            floating_action_button_location=FloatingActionButtonLocation.CENTER_DOCKED,
            resize_to_avoid_bottom_inset=True,
            extend_body=True,
            extend_body_behind_app_bar=True,
        )
        self.assertEqual(scaffold.props["floating_action_button_location"], "centerDocked")
        self.assertEqual(scaffold.props["resize_to_avoid_bottom_inset"], "true")
        self.assertEqual(scaffold.props["extend_body"], "true")
        self.assertEqual(scaffold.props["extend_body_behind_app_bar"], "true")

        ir = scaffold.to_ir_dict()
        self.assertEqual(ir["type"], "Scaffold")
        self.assertEqual(ir["props"]["floating_action_button_location"], "centerDocked")


if __name__ == "__main__":
    unittest.main()
