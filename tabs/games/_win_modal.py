from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Container


class WinModal(ModalScreen):
    """A pop-up shown when a game ends — winner or draw."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="win_modal_container"):
            yield Label(self._message, id="win_modal_message")
            yield Button("New Game", id="win_modal_new_game")
            yield Button("Close", id="win_modal_close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "win_modal_new_game":
            self.dismiss(True)   # caller restarts
        else:
            self.dismiss(False)  # caller just closes
