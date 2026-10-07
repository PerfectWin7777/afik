"""
Unit tests for newly added Flutter-mirror widgets:
GridView, Radio, RadioListTile, Tooltip, RichText, TextSpan,
CircleAvatar, LinearProgressIndicator, PopupMenuButton, RefreshIndicator,
AlertDialog, SimpleDialog.
"""

import unittest

from afik import (
    AlertDialog,
    Button,
    CircleAvatar,
    GridView,
    LinearProgressIndicator,
    PopupMenuButton,
    PopupMenuItem,
    Radio,
    RadioListTile,
    RefreshIndicator,
    RichText,
    SimpleDialog,
    Text,
    TextSpan,
    Tooltip,
)
from afik.core.render import render_tree_frame
from afik.core.widget_base import invoke_callback


class TestNewFlutterWidgets(unittest.TestCase):
    """Validates properties, signals, and IR serialization for new Flutter widgets."""

    def test_grid_view(self):
        items = [Text(f"Item {i}") for i in range(4)]
        grid = GridView.count(
            cross_axis_count=3,
            children=items,
            main_axis_spacing=12.0,
            cross_axis_spacing=12.0,
            shrink_wrap=True,
        )
        self.assertEqual(grid.widget_type, "GridView")
        self.assertEqual(grid.props["cross_axis_count"], "3")
        self.assertEqual(grid.props["main_axis_spacing"], "12.0")
        self.assertEqual(grid.props["shrink_wrap"], "true")
        self.assertEqual(len(grid.children), 4)

    def test_radio_and_radio_list_tile(self):
        selected_val = []

        def on_change(v):
            selected_val.append(v)

        r = Radio(value="opt1", group_value="opt1", on_change=on_change)
        self.assertEqual(r.widget_type, "Radio")
        self.assertEqual(r.props["value"], "opt1")
        self.assertEqual(r.props["group_value"], "opt1")

        invoke_callback(r.callback_id, {"value": "opt2"})
        self.assertEqual(selected_val, ["opt2"])

        r_tile = RadioListTile(
            value="theme_dark",
            group_value="theme_light",
            title="Dark Theme",
            subtitle="Enable dark mode across the app",
        )
        self.assertEqual(r_tile.widget_type, "RadioListTile")
        self.assertEqual(len(r_tile.children), 2)
        self.assertEqual(r_tile.children[0].props["slot"], "title")
        self.assertEqual(r_tile.children[1].props["slot"], "subtitle")

    def test_tooltip(self):
        tip = Tooltip("Add Item", child=Button("Add"))
        self.assertEqual(tip.widget_type, "Tooltip")
        self.assertEqual(tip.props["message"], "Add Item")
        self.assertEqual(len(tip.children), 1)

    def test_rich_text_and_text_span(self):
        clicks = []
        span1 = TextSpan("Normal text ")
        span2 = TextSpan(
            "Bold link",
            font_weight="bold",
            color="#1877F2",
            on_click=lambda: clicks.append("link_clicked"),
        )
        rich = RichText(spans=[span1, span2], text_align="center")

        self.assertEqual(rich.widget_type, "RichText")
        self.assertEqual(rich.props["text_align"], "center")
        self.assertEqual(len(rich.children), 2)

        invoke_callback(span2.callback_id, {})
        self.assertEqual(clicks, ["link_clicked"])

    def test_circle_avatar(self):
        avatar = CircleAvatar(
            radius=32.0,
            background_color="#E0E0E0",
            image_url="https://example.com/avatar.png",
            child=Text("JD"),
        )
        self.assertEqual(avatar.widget_type, "CircleAvatar")
        self.assertEqual(avatar.props["radius"], "32.0")
        self.assertEqual(avatar.props["image_url"], "https://example.com/avatar.png")
        self.assertEqual(len(avatar.children), 1)

    def test_linear_progress_indicator(self):
        bar = LinearProgressIndicator(value=0.75, color="#1877F2", min_height=6.0)
        self.assertEqual(bar.widget_type, "LinearProgressIndicator")
        self.assertEqual(bar.props["value"], "0.75")
        self.assertEqual(bar.props["min_height"], "6.0")

    def test_popup_menu_button(self):
        choices = []
        btn = PopupMenuButton(
            items=[
                PopupMenuItem(value="edit", child="Edit"),
                PopupMenuItem(value="delete", child="Delete"),
            ],
            on_selected=lambda v: choices.append(v),
            tooltip="Options",
        )
        self.assertEqual(btn.widget_type, "PopupMenuButton")
        self.assertEqual(len(btn.children), 2)

        invoke_callback(btn.callback_id, {"value": "delete"})
        self.assertEqual(choices, ["delete"])

    def test_refresh_indicator(self):
        refreshed = []
        ref = RefreshIndicator(
            child=Text("Pull me"),
            on_refresh=lambda: refreshed.append(True),
            color="#FF0000",
        )
        self.assertEqual(ref.widget_type, "RefreshIndicator")
        self.assertEqual(ref.props["color"], "#FF0000")
        self.assertEqual(len(ref.children), 1)

        invoke_callback(ref.callback_id, {})
        self.assertEqual(refreshed, [True])

    def test_alert_dialog_and_simple_dialog(self):
        dlg = AlertDialog(
            title="Confirm Action",
            content="Are you sure you want to proceed?",
            actions=[Button("Cancel"), Button("Confirm")],
        )
        self.assertEqual(dlg.widget_type, "AlertDialog")
        self.assertEqual(len(dlg.children), 4)  # title, content, 2 actions
        self.assertEqual(dlg.children[0].props["slot"], "title")
        self.assertEqual(dlg.children[1].props["slot"], "content")
        self.assertEqual(dlg.children[2].props["slot"], "action")

        sdlg = SimpleDialog(
            title="Select Option",
            children=[Text("Option A"), Text("Option B")],
        )
        self.assertEqual(sdlg.widget_type, "SimpleDialog")
        self.assertEqual(len(sdlg.children), 3)

    def test_protobuf_serialization(self):
        grid = GridView.count(
            cross_axis_count=2,
            children=[
                CircleAvatar(image_url="https://example.com/p1.png"),
                Tooltip("Info", child=LinearProgressIndicator(value=0.5)),
            ],
        )
        frame = render_tree_frame(grid)
        self.assertTrue(len(frame) > 10)
        self.assertEqual(frame[0], 0x01)  # MSG_RENDER_TREE


if __name__ == "__main__":
    unittest.main()
