"""
Unit test suite for Afik Gestures, Touch Interactions, and Implicit Animations.
"""

from __future__ import annotations

import unittest

from afik.core.constants import Alignment, Curves, DismissDirection
from afik.core.render import render_tree_frame
from afik.core.style import Duration
from afik.core.widget_base import invoke_callback
from afik.widgets.animations import (
    AnimatedAlign,
    AnimatedContainer,
    AnimatedCrossFade,
    AnimatedOpacity,
    AnimatedRotation,
    AnimatedScale,
    Hero,
)
from afik.widgets.gestures import Dismissible, GestureDetector, InkWell
from afik.widgets.widgets import Column, Container, Text


class TestGestures(unittest.TestCase):
    def test_gesture_detector_callbacks(self):
        events = []

        detector = GestureDetector(
            child=Text("Swipe or Tap me"),
            on_tap=lambda: events.append("tap"),
            on_double_tap=lambda: events.append("double_tap"),
            on_long_press=lambda: events.append("long_press"),
            on_swipe_left=lambda: events.append("swipe_left"),
            on_swipe_right=lambda: events.append("swipe_right"),
            on_swipe_up=lambda: events.append("swipe_up"),
            on_swipe_down=lambda: events.append("swipe_down"),
        )

        self.assertEqual(detector.widget_type, "GestureDetector")
        self.assertEqual(len(detector.children), 1)

        # Trigger each callback registered in props
        invoke_callback(detector.props["on_tap_callback_id"], {})
        invoke_callback(detector.props["on_double_tap_callback_id"], {})
        invoke_callback(detector.props["on_long_press_callback_id"], {})
        invoke_callback(detector.props["on_swipe_left_callback_id"], {})
        invoke_callback(detector.props["on_swipe_right_callback_id"], {})
        invoke_callback(detector.props["on_swipe_up_callback_id"], {})
        invoke_callback(detector.props["on_swipe_down_callback_id"], {})

        self.assertEqual(
            events,
            [
                "tap",
                "double_tap",
                "long_press",
                "swipe_left",
                "swipe_right",
                "swipe_up",
                "swipe_down",
            ],
        )

    def test_ink_well(self):
        taps = []
        ink = InkWell(
            child=Text("Click"),
            on_tap=lambda: taps.append("tapped"),
            splash_color="#1877F2",
            border_radius=12.0,
        )
        self.assertEqual(ink.widget_type, "InkWell")
        self.assertEqual(ink.props.get("splash_color"), "#1877F2")
        self.assertEqual(ink.props.get("border_radius"), "12.0")

        invoke_callback(ink.props["on_tap_callback_id"], {})
        self.assertEqual(taps, ["tapped"])

    def test_dismissible(self):
        dismissed = []
        item = Dismissible(
            key="cart_item_42",
            child=Text("Product in cart"),
            background=Container(color="#FF0000"),
            direction=DismissDirection.END_TO_START,
            on_dismissed=lambda dir: dismissed.append(dir),
        )
        self.assertEqual(item.widget_type, "Dismissible")
        self.assertEqual(item.props.get("key"), "cart_item_42")
        self.assertEqual(item.props.get("direction"), "end_to_start")
        self.assertEqual(len(item.children), 2)
        self.assertEqual(item.children[1].props.get("slot"), "background")

        invoke_callback(item.callback_id, {"direction": "end_to_start"})
        self.assertEqual(dismissed, ["end_to_start"])


class TestAnimations(unittest.TestCase):
    def test_hero(self):
        hero = Hero(tag="product_avatar", child=Text("Avatar"))
        self.assertEqual(hero.widget_type, "Hero")
        self.assertEqual(hero.props.get("tag"), "product_avatar")

    def test_animated_container(self):
        anim = AnimatedContainer(
            child=Text("Expanding Box"),
            width=200.0,
            height=150.0,
            color="#1877F2",
            border_radius=16.0,
            duration=Duration(milliseconds=500),
            curve=Curves.BOUNCE_OUT,
        )
        self.assertEqual(anim.widget_type, "AnimatedContainer")
        self.assertEqual(anim.props.get("width"), "200.0")
        self.assertEqual(anim.props.get("height"), "150.0")
        self.assertEqual(anim.props.get("color"), "#1877F2")
        self.assertEqual(anim.props.get("border_radius"), "16.0")
        self.assertEqual(anim.props.get("duration_ms"), "500")
        self.assertEqual(anim.props.get("curve"), "bounceOut")

    def test_animated_opacity(self):
        anim = AnimatedOpacity(
            child=Text("Fading"),
            opacity=0.75,
            duration=Duration(seconds=1),
            curve=Curves.EASE_IN,
        )
        self.assertEqual(anim.widget_type, "AnimatedOpacity")
        self.assertEqual(anim.props.get("opacity"), "0.75")
        self.assertEqual(anim.props.get("duration_ms"), "1000")
        self.assertEqual(anim.props.get("curve"), "easeIn")

    def test_animated_scale_and_rotation(self):
        scale = AnimatedScale(child=Text("Zoom"), scale=1.5)
        rot = AnimatedRotation(child=Text("Spin"), turns=0.25)

        self.assertEqual(scale.props.get("scale"), "1.5")
        self.assertEqual(scale.props.get("duration_ms"), "300")
        self.assertEqual(rot.props.get("turns"), "0.25")

    def test_animated_align_and_cross_fade(self):
        align = AnimatedAlign(
            child=Text("Moving"),
            alignment=Alignment.BOTTOM_RIGHT,
            duration=Duration(milliseconds=400),
        )
        self.assertEqual(align.props.get("alignment"), "bottom_right")
        self.assertEqual(align.props.get("duration_ms"), "400")

        cross = AnimatedCrossFade(
            first_child=Text("First"),
            second_child=Text("Second"),
            show_first=False,
            duration=Duration(milliseconds=250),
        )
        self.assertEqual(cross.props.get("show_first"), "false")
        self.assertEqual(cross.props.get("duration_ms"), "250")
        self.assertEqual(len(cross.children), 2)
        self.assertEqual(cross.children[0].props.get("slot"), "first_child")
        self.assertEqual(cross.children[1].props.get("slot"), "second_child")


class TestGesturesAndAnimationsSerialization(unittest.TestCase):
    def test_tree_serialization(self):
        tree = Column([
            GestureDetector(
                child=AnimatedContainer(
                    width=100.0,
                    height=100.0,
                    color="#4267B2",
                    duration=Duration(milliseconds=300),
                ),
                on_tap=lambda: None,
            ),
            Hero(tag="logo", child=Text("Afik")),
            Dismissible(
                key="item_1",
                child=Text("Dismiss me"),
            ),
        ])

        frame = render_tree_frame(tree)
        self.assertIsInstance(frame, bytes)
        self.assertEqual(frame[0], 0x01)


if __name__ == "__main__":
    unittest.main()
