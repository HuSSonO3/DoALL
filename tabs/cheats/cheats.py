from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, ListItem, ListView, TabPane
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.markup import escape
import os

from .db import get_db, init_db


# ---------------------------------------------------------------------------
# Modal Screens
# ---------------------------------------------------------------------------

class DeleteConfirmModal(ModalScreen):
    """Confirmation dialog before deleting."""

    def __init__(self, item_description: str):
        super().__init__()
        self.item_description = item_description

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Delete \"{self.item_description}\"?", id="cheats_delete_label"),
            Horizontal(
                Button("Cancel", variant="primary", id="cheats_delete_cancel"),
                Button("Delete", variant="error", id="cheats_delete_confirm"),
                id="cheats_delete_buttons",
            ),
            Label("Press Escape to close", id="cheats_small_label"),
            id="cheats_delete_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cheats_delete_confirm":
            self.dismiss(True)
        elif event.button.id == "cheats_delete_cancel":
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class SheetFormModal(ModalScreen):
    """Modal for adding or editing a cheat sheet."""

    def __init__(self, sheet_data=None):
        super().__init__()
        self.sheet_data = sheet_data
        self.is_edit = sheet_data is not None

    def compose(self) -> ComposeResult:
        yield Container(
            Label("[bold]Edit Sheet[/bold]" if self.is_edit else "[bold]New Sheet[/bold]",
                  id="cheats_form_title"),
            Label("Title"),
            Input(placeholder="e.g. Git Commands", id="cheats_sheet_title"),
            Button("Save", id="cheats_sheet_save"),
            Label("Press Escape to close", id="cheats_small_label"),
            id="cheats_form_container",
        )

    def on_mount(self) -> None:
        if self.is_edit:
            self.query_one("#cheats_sheet_title", Input).value = self.sheet_data["title"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "cheats_sheet_save":
            return

        title = self.query_one("#cheats_sheet_title", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        conn = get_db()
        if self.is_edit:
            try:
                conn.execute(
                    "UPDATE sheets SET title=? WHERE id=?",
                    (title, self.sheet_data["id"]),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                self.notify("A sheet with that title already exists.", severity="error")
                conn.close()
                return
        else:
            try:
                conn.execute(
                    "INSERT INTO sheets (title) VALUES (?)",
                    (title,),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                self.notify("A sheet with that title already exists.", severity="error")
                conn.close()
                return
        conn.close()

        self.dismiss(True)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class EntryFormModal(ModalScreen):
    """Modal for adding or editing a cheat sheet entry."""

    def __init__(self, sheet_id: int, entry_data=None):
        super().__init__()
        self.sheet_id = sheet_id
        self.entry_data = entry_data
        self.is_edit = entry_data is not None

    def compose(self) -> ComposeResult:
        yield Container(
            Label("[bold]Edit Entry[/bold]" if self.is_edit else "[bold]New Entry[/bold]",
                  id="cheats_form_title"),
            Label("Term / Command"),
            Input(placeholder="e.g. git clone <url>", id="cheats_entry_term"),
            Label("Definition"),
            Input(placeholder="What it does...", id="cheats_entry_def"),
            Button("Save", id="cheats_entry_save"),
            Label("Press Escape to close", id="cheats_small_label"),
            id="cheats_form_container",
        )

    def on_mount(self) -> None:
        if self.is_edit:
            self.query_one("#cheats_entry_term", Input).value = self.entry_data["term"]
            self.query_one("#cheats_entry_def", Input).value = self.entry_data["definition"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "cheats_entry_save":
            return

        term = self.query_one("#cheats_entry_term", Input).value.strip()
        definition = self.query_one("#cheats_entry_def", Input).value.strip()

        if not term:
            self.notify("Term is required.", severity="error")
            return
        if not definition:
            self.notify("Definition is required.", severity="error")
            return

        conn = get_db()
        if self.is_edit:
            conn.execute(
                "UPDATE entries SET term=?, definition=? WHERE id=?",
                (term, definition, self.entry_data["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO entries (sheet_id, term, definition) VALUES (?, ?, ?)",
                (self.sheet_id, term, definition),
            )
        conn.commit()
        conn.close()

        self.dismiss(True)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


# ---------------------------------------------------------------------------
# Main Widget
# ---------------------------------------------------------------------------

class CheatSheetWidget(Widget, can_focus=True):
    """Main widget: sheets on the left, entries on the right."""

    BINDINGS = [
        Binding("n", "add_entry", "New Entry"),
        Binding("e", "edit_entry", "Edit Entry"),
        Binding("d", "delete_entry", "Delete Entry"),
        Binding("a", "add_sheet", "New Sheet"),
        Binding("r", "rename_sheet", "Rename Sheet"),
        Binding("x", "delete_sheet", "Delete Sheet"),
    ]

    def __init__(self):
        super().__init__()
        self._current_sheet_id: int | None = None
        self._sheet_ids: list[int] = []

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                # --- Left panel: sheets ---
                Vertical(
                    Label("Sheets", id="cheats_sheets_heading"),
                    ListView(id="cheats_sheets_list"),
                    Horizontal(
                        Button("New Sheet", id="cheats_sheet_add", variant="primary"),
                        Button("Rename", id="cheats_sheet_edit"),
                        Button("Delete", id="cheats_sheet_delete", variant="error"),
                        id="cheats_sheet_buttons",
                    ),
                    id="cheats_left",
                ),
                # --- Right panel: entries ---
                Vertical(
                    Label("Entries", id="cheats_entries_heading"),
                    DataTable(id="cheats_entries_table"),
                    Horizontal(
                        Button("New Entry", id="cheats_entry_add", variant="primary"),
                        Button("Edit", id="cheats_entry_edit"),
                        Button("Delete", id="cheats_entry_delete", variant="error"),
                        Input(placeholder="Search entries...", id="cheats_search"),
                        id="cheats_entry_buttons",
                    ),
                    id="cheats_right",
                ),
                id="cheats_main",
            ),
            id="cheats_container",
        )

    def on_mount(self) -> None:
        init_db()
        self._refresh_sheets()
        self._setup_entries_table()

        # Select the first sheet automatically
        list_view = self.query_one("#cheats_sheets_list", ListView)
        if self._sheet_ids:
            list_view.index = 0
            self._current_sheet_id = self._sheet_ids[0]
            self._refresh_entries()
            self._update_entries_heading()

    def _setup_entries_table(self) -> None:
        table = self.query_one("#cheats_entries_table", DataTable)
        table.add_columns("Term / Command", "Definition")
        table.cursor_type = "row"
        table.tooltip = (
            "n: New Entry  e: Edit  d: Delete  a: New Sheet  r: Rename Sheet  x: Delete Sheet"
        )

    # ------------------------------------------------------------------
    # Sheet management
    # ------------------------------------------------------------------

    def _refresh_sheets(self) -> None:
        """Rebuild the ListView from the sheets table."""
        list_view = self.query_one("#cheats_sheets_list", ListView)
        # Store the currently selected sheet ID so we can restore selection
        previously_selected = self._current_sheet_id

        conn = get_db()
        sheets = conn.execute("SELECT id, title FROM sheets ORDER BY title").fetchall()
        conn.close()

        self._sheet_ids = [s["id"] for s in sheets]

        # Repopulate the ListView
        list_view.clear()
        for s in sheets:
            list_view.append(ListItem(Label(s["title"]), name=str(s["id"])))

        # Restore selection if the sheet still exists
        if previously_selected is not None and previously_selected in self._sheet_ids:
            new_index = self._sheet_ids.index(previously_selected)
            list_view.index = new_index
            self._current_sheet_id = previously_selected
        elif self._sheet_ids:
            list_view.index = 0
            self._current_sheet_id = self._sheet_ids[0]
        else:
            self._current_sheet_id = None

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """When the user navigates the sheets list, update the entries table."""
        if event.item is None or event.item.name is None:
            return
        sheet_id = int(event.item.name)
        if sheet_id != self._current_sheet_id:
            self._current_sheet_id = sheet_id
            self._refresh_entries()
            self._update_entries_heading()

    def _update_entries_heading(self) -> None:
        """Show the current sheet name in the entries heading."""
        heading = self.query_one("#cheats_entries_heading", Label)
        conn = get_db()
        row = conn.execute("SELECT title FROM sheets WHERE id=?", (self._current_sheet_id,)).fetchone()
        conn.close()
        if row:
            heading.update(f"Entries — {row['title']}")
        else:
            heading.update("Entries")

    # ------------------------------------------------------------------
    # Entry management
    # ------------------------------------------------------------------

    def _refresh_entries(self) -> None:
        """Reload the DataTable with entries for the current sheet."""
        table = self.query_one("#cheats_entries_table", DataTable)
        table.clear()

        if self._current_sheet_id is None:
            return

        conn = get_db()
        rows = conn.execute(
            "SELECT id, term, definition FROM entries WHERE sheet_id=? ORDER BY term",
            (self._current_sheet_id,),
        ).fetchall()
        conn.close()

        for row in rows:
            table.add_row(
                escape(row["term"]),
                escape(row["definition"]),
                key=str(row["id"]),
            )

        # Reset search input
        search = self.query_one("#cheats_search", Input)
        search.value = ""

    def _filter_entries(self, query: str) -> None:
        """Filter the displayed entries by a search query (client-side)."""
        table = self.query_one("#cheats_entries_table", DataTable)
        table.clear()

        if self._current_sheet_id is None:
            return

        conn = get_db()
        if query.strip():
            rows = conn.execute(
                "SELECT id, term, definition FROM entries WHERE sheet_id=? "
                "AND (term LIKE ? OR definition LIKE ?) ORDER BY term",
                (self._current_sheet_id, f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, term, definition FROM entries WHERE sheet_id=? ORDER BY term",
                (self._current_sheet_id,),
            ).fetchall()
        conn.close()

        for row in rows:
            table.add_row(
                escape(row["term"]),
                escape(row["definition"]),
                key=str(row["id"]),
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "cheats_search":
            self._filter_entries(event.value)

    # ------------------------------------------------------------------
    # Row helpers
    # ------------------------------------------------------------------

    def _get_selected_entry_id(self) -> str | None:
        table = self.query_one("#cheats_entries_table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row = table.ordered_rows[table.cursor_row]
        except IndexError:
            return None
        return row.key.value

    def _get_entry_term_from_db(self, entry_id: str) -> str:
        conn = get_db()
        row = conn.execute("SELECT term FROM entries WHERE id=?", (entry_id,)).fetchone()
        conn.close()
        return row["term"] if row else "this entry"

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        if bid == "cheats_sheet_add":
            self.action_add_sheet()
        elif bid == "cheats_sheet_edit":
            self.action_rename_sheet()
        elif bid == "cheats_sheet_delete":
            self.action_delete_sheet()
        elif bid == "cheats_entry_add":
            self.action_add_entry()
        elif bid == "cheats_entry_edit":
            self.action_edit_entry()
        elif bid == "cheats_entry_delete":
            self.action_delete_entry()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_add_sheet(self) -> None:
        self.app.push_screen(SheetFormModal(), self._on_sheet_saved)

    def action_rename_sheet(self) -> None:
        if self._current_sheet_id is None:
            self.notify("No sheet selected.", severity="warning")
            return

        conn = get_db()
        row = conn.execute("SELECT * FROM sheets WHERE id=?", (self._current_sheet_id,)).fetchone()
        conn.close()

        if row:
            self.app.push_screen(SheetFormModal(dict(row)), self._on_sheet_saved)

    def action_delete_sheet(self) -> None:
        if self._current_sheet_id is None:
            self.notify("No sheet selected.", severity="warning")
            return

        conn = get_db()
        row = conn.execute("SELECT title FROM sheets WHERE id=?", (self._current_sheet_id,)).fetchone()
        conn.close()

        if row:
            self.app.push_screen(
                DeleteConfirmModal(f"sheet '{row['title']}' and all its entries"),
                self._on_sheet_delete_confirmed,
            )

    def _on_sheet_saved(self, result) -> None:
        if result:
            self._refresh_sheets()
            self._refresh_entries()
            self._update_entries_heading()

    def _on_sheet_delete_confirmed(self, confirmed) -> None:
        if not confirmed:
            return
        conn = get_db()
        conn.execute("DELETE FROM sheets WHERE id=?", (self._current_sheet_id,))
        conn.commit()
        conn.close()

        self._current_sheet_id = None
        self._refresh_sheets()
        # Clear entries table
        table = self.query_one("#cheats_entries_table", DataTable)
        table.clear()

    def action_add_entry(self) -> None:
        if self._current_sheet_id is None:
            self.notify("Select a sheet first.", severity="warning")
            return
        self.app.push_screen(EntryFormModal(self._current_sheet_id), self._on_entry_saved)

    def action_edit_entry(self) -> None:
        entry_id = self._get_selected_entry_id()
        if entry_id is None:
            self.notify("No entry selected.", severity="warning")
            return

        conn = get_db()
        row = conn.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
        conn.close()

        if row:
            self.app.push_screen(
                EntryFormModal(self._current_sheet_id, dict(row)),
                self._on_entry_saved,
            )

    def action_delete_entry(self) -> None:
        entry_id = self._get_selected_entry_id()
        if entry_id is None:
            self.notify("No entry selected.", severity="warning")
            return

        term = self._get_entry_term_from_db(entry_id)
        self.app.push_screen(
            DeleteConfirmModal(term),
            self._on_entry_delete_confirmed(entry_id),
        )

    def _on_entry_delete_confirmed(self, entry_id: str):
        def callback(confirmed):
            if confirmed:
                conn = get_db()
                conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
                conn.commit()
                conn.close()
                self._refresh_entries()

        return callback

    def _on_entry_saved(self, result) -> None:
        if result:
            self._refresh_entries()


# ---------------------------------------------------------------------------
# TabPane wrapper
# ---------------------------------------------------------------------------

class CheatSheetTab(TabPane):
    """TabPane wrapper for the Cheat Sheet module."""

    DEFAULT_CSS = open(os.path.join(os.path.dirname(__file__), "cheats.tcss")).read()

    def compose(self) -> ComposeResult:
        yield CheatSheetWidget()
