"""Modal screens for the Habit Tracker module."""

from textual.app import ComposeResult
from textual.widgets import Input, Button, Label
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen


# ═══════════════════════════════════════════════════════════════
# Add / Edit Habit Modal
# ═══════════════════════════════════════════════════════════════

class HabitFormModal(ModalScreen):
    """Add or rename a habit."""

    def __init__(self, current_name: str = ""):
        super().__init__()
        self._current_name = current_name
        self._is_edit = bool(current_name)

    def compose(self) -> ComposeResult:
        title = "Edit Habit" if self._is_edit else "Add Habit"
        with Container(id="habit_form_container"):
            yield Label(f"[bold]{title}[/]", id="habit_form_title")
            yield Input(
                placeholder="Habit name...",
                value=self._current_name,
                id="habit_form_name",
            )
            with Horizontal(id="habit_form_buttons"):
                yield Button("Save", variant="primary", id="habit_form_save")
            yield Label("Press Escape to close", id="habit_small_label")

    def _try_save(self):
        name = self.query_one("#habit_form_name", Input).value.strip()
        if not name:
            self.notify("Habit name is required.", severity="error")
            return
        self.dismiss(name)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "habit_form_save":
            self._try_save()

    def on_input_submitted(self, event: Input.Submitted):
        self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


# ═══════════════════════════════════════════════════════════════
# Delete Confirm Modal
# ═══════════════════════════════════════════════════════════════

class HabitDeleteConfirmModal(ModalScreen):
    """Confirm before deleting a habit and all its history."""

    def __init__(self, habit_name: str):
        super().__init__()
        self._habit_name = habit_name

    def compose(self) -> ComposeResult:
        with Container(id="habit_del_container"):
            yield Label(
                f'Delete "[bold]{self._habit_name}[/]"?\n'
                f"[dim]All entries for this habit will be removed.[/]",
                id="habit_del_label",
            )
            with Horizontal(id="habit_del_buttons"):
                yield Button("Delete", variant="error", id="habit_del_confirm")
            yield Label("Press Escape to close", id="habit_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "habit_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)
