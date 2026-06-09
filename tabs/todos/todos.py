"""Todo list — widget and tab wrapper."""

from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Label, TabPane
from textual.widget import Widget
from textual.containers import Container
from textual.binding import Binding

from .db import init_db, get_db, PRIORITY_COLORS, PRIORITY_LABELS, STATUS_ICONS, STATUS_CYCLE
from .modals import DeleteConfirmModal, TodoFormModal


class TodoWidget(Widget, can_focus=True):
    """Main todo list: DataTable with status icons, priority colors, and due dates."""

    BINDINGS = [
        Binding("n", "add_todo", "Add"),
        Binding("e", "edit_todo", "Edit"),
        Binding("d", "delete_todo", "Delete"),
        Binding("t", "toggle_status", "Toggle"),
    ]

    STATUS_COL = "✓"

    def compose(self) -> ComposeResult:
        yield Container(
            Label("☐ Todo    ◐ In Progress    ☑ Done", id="todo_legend"),
            DataTable(id="todo_table"),
            Button("Add Todo", id="todo_add"),
            id="todo_container",
        )

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
    def compose(self) -> ComposeResult:
        yield TodoWidget()
