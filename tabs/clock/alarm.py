from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label, Static, TabbedContent , TabPane, Button, DataTable, Digits
from textual.widget import Widget
from textual.containers import Container, Horizontal, VerticalScroll
import sqlite3

class AlarmWidget(Widget):
    def render(self) -> str:
        return "I am a custom alarm widget!"
