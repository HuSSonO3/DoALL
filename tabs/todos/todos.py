from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select, TabPane
from textual.widget import Widget
from textual.containers import Container, Horizontal
from textual.binding import Binding
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'todo',
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        )
    """)
    conn.commit()
    conn.close()


PRIORITY_COLORS = {0: "green", 1: "yellow", 2: "red"}
PRIORITY_LABELS = {0: "Low", 1: "Medium", 2: "High"}
STATUS_ICONS = {"todo": "☐", "in_progress": "◐", "done": "☑"}
STATUS_CYCLE = {"todo": "in_progress", "in_progress": "done", "done": "todo"}


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
        self.todo_data = todo_data  # None = add mode, dict = edit mode
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
        """Pre-populate fields when editing an existing todo."""
        if self.is_edit:
            self.query_one("#todo_form_title_input", Input).value = self.todo_data["title"]
            self.query_one("#todo_form_desc_input", Input).value = self.todo_data["description"] or ""
            if self.todo_data["due_date"]:
                self.query_one("#todo_form_due", Input).value = self.todo_data["due_date"]
            # Defer Select value assignment until widget is fully ready
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
                self.notify(
                    "Due date must be today or in the future.",
                    severity="error",
                )
                return
            # Normalize: pad single-digit month/day with leading zero
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
        """Return True if value matches YYYY/MM/DD and is a real calendar date."""
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
        """Return True if value is today or in the future."""
        y, m, d = map(int, value.split("/"))
        return datetime(y, m, d).date() >= datetime.now().date()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class TodoWidget(Widget, can_focus=True):
    """Main todo list: DataTable with status icons, priority colors, and due dates."""

    BINDINGS = [
        Binding("n", "add_todo", "Add"),
        Binding("e", "edit_todo", "Edit"),
        Binding("d", "delete_todo", "Delete"),
        Binding("t", "toggle_status", "Toggle"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("☐ Todo    ◐ In Progress    ☑ Done", id="todo_legend"),
            DataTable(id="todo_table"),
            Button("Add Todo", id="todo_add"),
            id="todo_container",
        )

    STATUS_COL = "✓"

    def on_mount(self) -> None:
        init_db()
        table = self.query_one("#todo_table", DataTable)
        table.add_columns(self.STATUS_COL, "Title", "Priority", "Due", "Description")
        table.cursor_type = "row"
        table.tooltip = (
            "☐ Todo  |  ◐ In Progress  |  ☑ Done\n"
            "n: Add  e: Edit  d: Delete  t: Toggle"
        )
        self.refresh_table()

    def refresh_table(self, keep_focus_id: str | None = None) -> None:
        table = self.query_one("#todo_table", DataTable)
        table.clear()
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM todos ORDER BY status ASC, priority DESC, created_at ASC"
        ).fetchall()
        conn.close()

        for row in rows:
            icon = STATUS_ICONS.get(row["status"], "☐")
            priority_label = PRIORITY_LABELS.get(row["priority"], "Low")
            color = PRIORITY_COLORS.get(row["priority"], "green")
            due = row["due_date"] if row["due_date"] else "—"
            desc = row["description"] or "—"
            if len(desc) > 40:
                desc = desc[:37] + "..."

            table.add_row(
                icon,
                row["title"],
                f"[{color}]{priority_label}[/]",
                due,
                desc,
                key=str(row["id"]),
            )

        # Restore cursor to the row matching keep_focus_id, if provided
        if keep_focus_id is not None:
            for idx, ordered_row in enumerate(table.ordered_rows):
                if ordered_row.key.value == keep_focus_id:
                    table.move_cursor(row=idx)
                    break

    def _get_selected_id(self) -> str | None:
        table = self.query_one("#todo_table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key = table.ordered_rows[table.cursor_row]
        except IndexError:
            return None
        return row_key.key.value

    def _get_selected_title(self) -> str | None:
        table = self.query_one("#todo_table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key = table.ordered_rows[table.cursor_row]
        except IndexError:
            return None
        # Title is the second column (index 1)
        return str(row_key[1])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "todo_add":
            self.app.push_screen(TodoFormModal(), self._on_todo_saved)

    def _on_todo_saved(self, result) -> None:
        if result:
            self.refresh_table()

    def action_add_todo(self) -> None:
        self.app.push_screen(TodoFormModal(), self._on_todo_saved)

    def action_edit_todo(self) -> None:
        todo_id = self._get_selected_id()
        if todo_id is None:
            self.notify("No todo selected.", severity="warning")
            return

        conn = get_db()
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        conn.close()

        if row:
            self.app.push_screen(TodoFormModal(dict(row)), self._on_todo_saved)

    def action_delete_todo(self) -> None:
        todo_id = self._get_selected_id()
        if todo_id is None:
            self.notify("No todo selected.", severity="warning")
            return

        title = self._get_selected_title()
        self.app.push_screen(DeleteConfirmModal(title or ""), self._on_delete_confirmed(todo_id))

    def _on_delete_confirmed(self, todo_id: str):
        """Return a callback that deletes the todo if confirmed."""

        def callback(confirmed):
            if confirmed:
                conn = get_db()
                conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
                conn.commit()
                conn.close()
                self.refresh_table()

        return callback

    def action_toggle_status(self) -> None:
        todo_id = self._get_selected_id()
        if todo_id is None:
            self.notify("No todo selected.", severity="warning")
            return

        conn = get_db()
        row = conn.execute("SELECT status FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row:
            new_status = STATUS_CYCLE.get(row["status"], "todo")
            completed_at = None
            if new_status == "done":
                completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "UPDATE todos SET status = ?, completed_at = ? WHERE id = ?",
                (new_status, completed_at, todo_id),
            )
            conn.commit()
        conn.close()
        self.refresh_table(keep_focus_id=todo_id)


class TodoTab(TabPane):
    """TabPane wrapper for the Todo module."""

    def compose(self) -> ComposeResult:
        yield TodoWidget()
