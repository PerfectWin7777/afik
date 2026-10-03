"""
PyFlutter / Flarix Example: Modern Material 3 Counter Application.
Demonstrates:
- Clean Component-based UI Architecture
- Reactive state management with self.update()
- Material 3 Scaffold, AppBar, Card, and Typography
- Elevated, Outlined, and FloatingAction buttons
"""

from __future__ import annotations

import sys
from pathlib import Path

# Auto-detect framework root if running directly as a script
_framework_dir = Path(__file__).resolve().parents[2] / "py_framework"
if _framework_dir.exists() and str(_framework_dir) not in sys.path:
    sys.path.insert(0, str(_framework_dir))

from pyflutter import (
    AppBar,
    Card,
    Center,
    Colors,
    Column,
    Component,
    Container,
    CrossAxisAlignment,
    ElevatedButton,
    FloatingActionButton,
    FontWeight,
    Icon,
    Icons,
    MainAxisAlignment,
    OutlinedButton,
    Row,
    Scaffold,
    SizedBox,
    Text,
    TextButton,
    run,
)


class CounterApp(Component):
    """Modern reactive Material 3 Counter Application."""

    def __init__(self):
        super().__init__()
        self.count: int = 0

    def increment(self):
        self.count += 1
        self.update()

    def decrement(self):
        if self.count > 0:
            self.count -= 1
            self.update()

    def reset(self):
        self.count = 0
        self.update()

    def build(self):
        status_text = "Pair" if self.count % 2 == 0 else "Impair"
        status_color = Colors.EMERALD if self.count % 2 == 0 else Colors.WARNING

        counter_card = Card(
            Column([
                Text("VALEUR DU COMPTEUR", font_size=12, font_weight=FontWeight.BOLD, color=Colors.GREY),
                SizedBox(height=12),
                Text(
                    str(self.count),
                    font_size=64,
                    font_weight=FontWeight.BOLD,
                    color=Colors.NAVY,
                ),
                SizedBox(height=8),
                Container(
                    Text(f"Nombre {status_text}", font_size=12, font_weight=FontWeight.BOLD, color=status_color),
                    padding=6,
                    border_radius=8,
                    background_color=Colors.with_opacity(status_color, 0.15),
                ),
                SizedBox(height=24),
                Row([
                    OutlinedButton(
                        text="-1",
                        icon=Icons.REMOVE,
                        on_click=self.decrement,
                    ),
                    SizedBox(width=12),
                    TextButton(
                        text="Réinitialiser",
                        icon=Icons.REFRESH,
                        on_click=self.reset,
                    ),
                    SizedBox(width=12),
                    ElevatedButton(
                        text="+1",
                        icon=Icons.ADD,
                        on_click=self.increment,
                        background_color=Colors.BLUE,
                        color=Colors.WHITE,
                    ),
                ], main_axis_alignment=MainAxisAlignment.CENTER),
            ], cross_axis_alignment=CrossAxisAlignment.CENTER),
            padding=24,
            elevation=3,
            border_radius=16,
        )

        app_bar = AppBar(
            title=Text("Flarix Counter", font_size=20, font_weight=FontWeight.BOLD, color=Colors.WHITE),
            background_color=Colors.BLUE,
            elevation=1,
        )

        fab = FloatingActionButton(
            icon=Icons.ADD,
            tooltip="Incrémenter",
            background_color=Colors.BLUE,
            color=Colors.WHITE,
            on_click=self.increment,
        )

        return Scaffold(
            app_bar=app_bar,
            body=Center(
                Container(counter_card, padding=16)
            ),
            floating_action_button=fab,
            background_color=Colors.SCAFFOLD_BACKGROUND,
        )


# Backward compatibility alias
App = CounterApp

if __name__ == "__main__":
    run(CounterApp())
