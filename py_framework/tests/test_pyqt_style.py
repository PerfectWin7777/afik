"""
Unit tests for the PyQt/PySide OOP paradigm in PyFlutter.
Validates imperative layout assembly, QtSignal connections, mutators/getters,
Slider support, smart Component.build() resolution, and Protobuf IR serialization.
"""

import unittest
from pyflutter import (
    Column,
    Row,
    Text,
    Button,
    ElevatedButton,
    OutlinedButton,
    TextButton,
    IconButton,
    TextField,
    Switch,
    Checkbox,
    Slider,
    DropdownButton,
    Scaffold,
    AppBar,
    Component,
    MainWindow,
    QtSignal,
)
from pyflutter.core.widget_base import invoke_callback, _callback_registry


class TestPyQtLayoutAssembly(unittest.TestCase):
    """Tests imperative child management on Column/Row/Widget."""

    def test_imperative_chaining_and_aliases(self):
        col = Column()
        self.assertEqual(col.count(), 0)

        # Chaining add_widget and Qt alias addWidget
        lbl = Text("First")
        btn = Button("Click")
        col.add_widget(lbl).addWidget(btn)
        self.assertEqual(col.count(), 2)
        self.assertIs(col.item_at(0), lbl)
        self.assertIs(col.itemAt(1), btn)

        # Spacing and Stretch
        col.add_spacing(12.0)
        col.add_stretch(flex=2)
        col.add_divider(thickness=2.0, indent=16.0, end_indent=16.0)
        self.assertEqual(col.count(), 5)
        self.assertEqual(col.children[2].widget_type, "SizedBox")
        self.assertEqual(col.children[2].props["height"], "12.0")
        self.assertEqual(col.children[3].widget_type, "Spacer")
        self.assertEqual(col.children[3].props["flex"], "2")
        self.assertEqual(col.children[4].widget_type, "Divider")
        self.assertEqual(col.children[4].props["indent"], "16.0")
        self.assertEqual(col.children[4].props["end_indent"], "16.0")

        # add_widgets
        col.add_widgets(Text("A"), Text("B"))
        self.assertEqual(col.count(), 7)

        # insert_widget
        inserted = Text("Inserted At 0")
        col.insert_widget(0, inserted)
        self.assertEqual(col.count(), 8)
        self.assertIs(col.item_at(0), inserted)

        # remove_widget
        col.remove_widget(inserted)
        self.assertEqual(col.count(), 7)
        self.assertIs(col.item_at(0), lbl)

        # clear
        col.clear()
        self.assertEqual(col.count(), 0)


class TestQtSignalSystem(unittest.TestCase):
    """Tests QtSignal connect, disconnect, emit, and multiple slots."""

    def test_button_clicked_signal(self):
        btn = Button("Test")
        clicks = []

        def on_click():
            clicks.append("clicked_1")

        def on_click_2():
            clicks.append("clicked_2")

        btn.clicked.connect(on_click)
        btn.clicked.connect(on_click_2)

        # Verify callback registered in PyFlutter engine
        self.assertTrue(btn.callback_id)
        self.assertIn(btn.callback_id, _callback_registry)

        # Simulate event coming across the Flutter Bridge
        invoke_callback(btn.callback_id, {})
        self.assertEqual(clicks, ["clicked_1", "clicked_2"])

        # Manual emit
        btn.clicked.emit()
        self.assertEqual(len(clicks), 4)

        # Disconnect specific slot
        btn.clicked.disconnect(on_click)
        btn.clicked.emit()
        self.assertEqual(clicks[-1], "clicked_2")
        self.assertEqual(len(clicks), 5)

        # Disconnect all
        btn.clicked.disconnect()
        btn.clicked.emit()
        self.assertEqual(len(clicks), 5)

    def test_text_field_text_changed_signal(self):
        field = TextField(value="init")
        received = []

        def on_text(new_val):
            received.append(new_val)

        field.textChanged.connect(on_text)

        # Simulate text event from native Flutter engine
        invoke_callback(field.callback_id, {"value": "Hello World"})
        self.assertEqual(received, ["Hello World"])
        self.assertEqual(field.text(), "Hello World")
        self.assertEqual(field.props["value"], "Hello World")

        # Mutator setText / clear
        field.setText("Changed via method")
        self.assertEqual(field.text(), "Changed via method")
        field.clear()
        self.assertEqual(field.text(), "")

    def test_text_field_return_pressed_signal(self):
        field = TextField()
        submitted = []

        field.returnPressed.connect(lambda val: submitted.append(val))
        submit_cid = field.props.get("submit_callback_id")
        self.assertTrue(submit_cid)

        invoke_callback(submit_cid, {"value": "query string"})
        self.assertEqual(submitted, ["query string"])

    def test_switch_and_checkbox_toggled_signal(self):
        sw = Switch(value=False)
        self.assertFalse(sw.isChecked())

        toggles = []
        sw.toggled.connect(lambda checked: toggles.append(checked))

        # Simulate native Flutter toggle event
        invoke_callback(sw.callback_id, {"value": "true"})
        self.assertTrue(sw.isChecked())
        self.assertEqual(toggles, [True])

        # Imperative toggle
        sw.toggle()
        self.assertFalse(sw.isChecked())
        sw.setChecked(True)
        self.assertTrue(sw.isChecked())

        # Checkbox
        cb = Checkbox(value=False)
        cb_states = []
        cb.stateChanged.connect(lambda val: cb_states.append(val))
        invoke_callback(cb.callback_id, {"value": "true"})
        self.assertTrue(cb.isChecked())
        self.assertEqual(cb_states, [True])

    def test_slider_value_changed_signal(self):
        slider = Slider(value=0.25, min=0.0, max=1.0)
        self.assertEqual(slider.value(), 0.25)

        vals = []
        slider.valueChanged.connect(lambda v: vals.append(v))

        # Simulate event from Flutter
        invoke_callback(slider.callback_id, {"value": "0.75"})
        self.assertEqual(slider.value(), 0.75)
        self.assertEqual(vals, [0.75])

        slider.setValue(0.5)
        self.assertEqual(slider.value(), 0.5)
        self.assertEqual(slider.props["value"], "0.5")


class TestSmartComponentBuildFallback(unittest.TestCase):
    """Tests writing complete components in PyQt style without overriding build()."""

    def test_component_with_layout_attribute(self):
        class CounterApp(Component):
            def __init__(self):
                super().__init__()
                self.count = 0
                self.layout = Column()
                self.label = Text("Count: 0")
                self.btn = Button("Add")
                self.btn.clicked.connect(self.increment)

                self.layout.add_widget(self.label)
                self.layout.add_widget(self.btn)

            def increment(self):
                self.count += 1
                self.label.setText(f"Count: {self.count}")

        app = CounterApp()
        # build() is not overridden, but automatically resolves self.layout!
        tree = app.build()
        self.assertEqual(tree.widget_type, "Column")
        self.assertEqual(len(tree.children), 2)
        self.assertEqual(tree.children[0].props["value"], "Count: 0")

        # Simulate click
        app.btn.clicked.emit()
        self.assertEqual(app.count, 1)
        self.assertEqual(app.label.text(), "Count: 1")

    def test_component_with_direct_add_widget(self):
        class DirectComponent(MainWindow):
            def __init__(self):
                super().__init__()
                self.add_widget(Text("Item 1"))
                self.add_spacing(10)
                self.add_widget(Text("Item 2"))

        comp = DirectComponent()
        tree = comp.build()
        self.assertEqual(tree.widget_type, "Column")
        self.assertEqual(len(tree.children), 3)

    def test_component_auto_scaffold_synthesis(self):
        class FullWindow(MainWindow):
            def __init__(self):
                super().__init__()
                self.app_bar = "My Dashboard"
                self.column = Column()
                self.column.add_widget(Text("Dashboard body"))

        win = FullWindow()
        tree = win.build()
        self.assertEqual(tree.widget_type, "Scaffold")
        app_bar_nodes = [c for c in tree.children if c.props.get("slot") == "app_bar"]
        body_nodes = [c for c in tree.children if c.props.get("slot") == "body"]
        self.assertEqual(len(app_bar_nodes), 1)
        self.assertEqual(len(body_nodes), 1)
        self.assertEqual(app_bar_nodes[0].widget_type, "AppBar")
        self.assertEqual(app_bar_nodes[0].props["title"], "My Dashboard")
        self.assertEqual(body_nodes[0].widget_type, "Column")


class TestCleanNamespaceAndIrDict(unittest.TestCase):
    """Tests clean namespace and Protobuf IR dictionary export."""

    def test_main_window_alias(self):
        self.assertIs(MainWindow, Component)

    def test_to_ir_dict_serialization(self):
        col = Column()
        lbl = Text("User Name:")
        inp = TextField(placeholder="Enter name")
        slider = Slider(value=0.5, min=0.0, max=1.0)
        btn = Button("Save")
        btn.clicked.connect(lambda: None)

        col.addWidget(lbl)
        col.addSpacing(16)
        col.addWidget(inp)
        col.addWidget(slider)
        col.addWidget(btn)

        ir = col.to_ir_dict()
        self.assertEqual(ir["type"], "Column")
        self.assertEqual(len(ir["children"]), 5)
        self.assertEqual(ir["children"][0]["type"], "Text")
        self.assertEqual(ir["children"][0]["props"]["value"], "User Name:")
        self.assertEqual(ir["children"][1]["type"], "SizedBox")
        self.assertIn(ir["children"][1]["props"]["height"], ("16", "16.0"))
        self.assertEqual(ir["children"][2]["type"], "TextField")
        self.assertEqual(ir["children"][3]["type"], "Slider")
        self.assertEqual(ir["children"][3]["props"]["value"], "0.5")
        self.assertEqual(ir["children"][4]["type"], "Button")
        self.assertTrue(ir["children"][4]["callback_id"])


class TestMaterialAppReactiveRootAndCallbacks(unittest.TestCase):
    """Tests reactive MaterialApp root updates and custom callback registration."""

    def test_material_app_root_update(self):
        from pyflutter import MaterialApp
        from pyflutter.core.navigation import Navigator

        scaffold1 = Scaffold(body=Text("Tab 0"))
        app1 = MaterialApp(scaffold1)
        self.assertIs(app1.children[0], scaffold1)

        scaffold2 = Scaffold(body=Text("Tab 1"))
        app2 = MaterialApp(scaffold2)
        self.assertIs(app2.children[0], scaffold2)
        self.assertEqual(app2.children[0].children[0].props.get("value"), "Tab 1")

    def test_register_callback_custom_id_and_single_execution(self):
        from pyflutter.core.widget_base import _register_callback, _call_callable

        # Multi-signature test
        cid = _register_callback("custom_id_123", lambda: "ok")
        self.assertEqual(cid, "custom_id_123")

        # Zero-arg slot executed once
        call_count = 0
        def slot():
            nonlocal call_count
            call_count += 1
            raise ValueError("Something broke inside slot")

        with self.assertRaises(ValueError):
            _call_callable(slot, value="ignored")
        self.assertEqual(call_count, 1)


if __name__ == "__main__":
    unittest.main()
