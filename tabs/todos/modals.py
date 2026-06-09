"""Todo modals — delete confirmation and add/edit form."""

from datetime import datetime

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select
from textual.containers import Container, Horizontal

from .db import get_db


class DeleteConfirmModal(ModalScreen):
    """Confirmation dialog before deleting a todo."""

    def __init__(self, todo_title: str):
        super().__init__()
        self.todo_title = todo_title

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Delete \"{self.todo_title}\"?", id="todo_delete_label"),
            Horizontal(
                Button("Cancel", variant="primary", id="todo_delete_cancel"),
                Button("Delete", variant="error", id="todo_delete_confirm"),
                id="todo_delete_buttons",
            ),
            Label("Press Escape to close", id="small_label"),
            id="todo_delete_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "todo_delete_confirm":
            self.dismiss(True)
        elif event.button.id == "todo_delete_cancel":
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class TodoFormModal(ModalScreen):
    """Modal for adding or editing a todo. Pass todo_data to edit, None to add."""

    def __init__(self, todo_data=None):
        super().__init__()
        self.todo_data = todo_data
        self.is_edit = todo_data is not None

    def compose(self) -> ComposeResult:
        yield Container(
            Label("[bold]Edit Todo[/bold]" if self.is_edit else "[bold]Add Todo[/bold]", id="todo_form_title"),
            Label("Title"),
            Input(placeholder="What needs to be done?", id="todo_form_title_input"),
            Label("Description"),
            Input(placeholder="Optional notes...", id="todo_form_desc_input"),
            Label("Priority"),
            Select(
                [("Low", 0), ("Medium", 1), ("High", 2)],
                prompt="Priority",
                id="todo_form_priority",
            ),
            Label("Due Date"),
            Input(placeholder="YYYY/MM/DD (optional)", id="todo_form_due"),
            Button("Save", id="todo_form_save"),
            Label("Press Escape to close", id="small_label"),
            id="todo_form_container",
        )

    def on_mount(self) -> None:
        if self.is_edit:
            self.query_one("#todo_form_title_input", Input).value = self.todo_data["title"]
            self.query_one("#todo_form_desc_input", Input).value = self.todo_data["description"] or ""
            if self.todo_data["due_date"]:
                self.query_one("#todo_form_due", Input).value = self.todo_data["due_date"]
            self.call_after_refresh(
                lambda: setattr(
                    self.query_one("#todo_form_priority", Select), "value", self.todo_data["priority"]
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "todo_form_save":
            return

        title = self.query_one("#todo_form_title_input", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        description = self.query_one("#todo_form_desc_input", Input).value.strip()
        priority = self.query_one("#todo_form_priority", Select).value
        if priority == Select.BLANK or priority == Select.NULL:
            priority = 0
        due_date = self.query_one("#todo_form_due", Input).value.strip() or None

        if due_date is not None:
            if not self._is_valid_date(due_date):
                self.notify(
                    "Due date must be YYYY/MM/DD (e.g. 2026/12/25) or left empty.",
                    severity="error",
                )
                return
            if not self._is_future_date(due_date):
                self.notify("Due date must be today or in the future.", severity="error")
                return
            y, m, d = due_date.split("/")
            due_date = f"{y}/{int(m):02d}/{int(d):02d}"

        conn = get_db()
        if self.is_edit:
            conn.execute(
                "UPDATE todos SET title=?, description=?, priority=?, due_date=? WHERE id=?",
                (title, description, priority, due_date, self.todo_data["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO todos (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
                (title, description, priority, due_date),
            )
        conn.commit()
        conn.close()

        self.dismiss(True)

    @staticmethod
    def _is_valid_date(value: str) -> bool:
        parts = value.split("/")
        if len(parts) != 3:
            return False
        if not all(p.isdigit() for p in parts):
            return False
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        if m < 1 or m > 12 or d < 1 or d > 31:
            return False
        try:
            datetime(y, m, d)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_future_date(value: str) -> bool:
        y, m, d = map(int, value.split("/"))
        return datetime(y, m, d).date() >= datetime.now().date()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
