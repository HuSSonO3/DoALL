from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label
from textual.containers import Container, Horizontal, VerticalScroll
import os
import sqlite3

class TimerTab(TabPane):
        
    DEFAULT_CSS = open(os.path.join(os.path.dirname(__file__), "timer.tcss")).read()

    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder(self.test(), id="template_p1"),)
        
            
