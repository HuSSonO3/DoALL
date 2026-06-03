import random

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, Digits
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding


class RandomPickerWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("enter", "roll", "Roll"),
        Binding("r", "roll", "Roll"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="rp_container"):
            yield Label("[bold]Random Number Generator[/]", id="rp_title")

            with Horizontal(id="rp_input_row"):
                yield Input(placeholder="From", value="1", id="rp_from")
                yield Label("to", id="rp_to_label")
                yield Input(placeholder="To", value="100", id="rp_to")
                yield Button("Roll", variant="primary", id="rp_roll_btn")

            yield Digits("", id="rp_result")

    def on_mount(self):
        self.query_one("#rp_from", Input).focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "rp_roll_btn":
            self.action_roll()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id in ("rp_from", "rp_to"):
            self.action_roll()

    def action_roll(self):
        from_str = self.query_one("#rp_from", Input).value.strip()
        to_str = self.query_one("#rp_to", Input).value.strip()

        try:
            lo = int(from_str)
            hi = int(to_str)
        except ValueError:
            self.notify("Both values must be whole numbers.", severity="error")
            return

        if lo >= hi:
            self.notify("From must be less than To.", severity="error")
            return

        result = random.randint(lo, hi)
        self.query_one("#rp_result", Digits).update(str(result))


class RandomPickerTab(TabPane):
    def compose(self) -> ComposeResult:
        yield RandomPickerWidget()
