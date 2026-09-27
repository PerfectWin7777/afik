"""
PyFlutter POC example: a counter.

Demonstrates the enforced entry-point convention (vision doc §5.2):
a main.py exposing an `App` class recognized by `pyflutter run`.
"""

from pyflutter import Column, Text, Button


class App:
    def __init__(self):
        self.count = 0
        self.text = Text(str(self.count))
        self.button = Button("+1", on_click=self.increment)

    def build(self):
        # self.text / self.button persist across calls — only the
        # container wrapping them is rebuilt each time, which is fine
        # since containers carry no callback identity of their own.
        return Column([self.text, self.button])

    def increment(self):
        self.count += 1
        self.text.set_text(str(self.count))
        print(f"[app] count is now {self.count}")

