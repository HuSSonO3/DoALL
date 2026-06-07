from datetime import datetime, date

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, DataTable, Digits
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.binding import Binding

from .db import init_db, add_event, get_events, delete_event, days_until


class EventFormModal(ModalScreen):
    """Add a new countdown event."""

    def compose(self) -> ComposeResult:
        with Container(id="cd_form_container"):
            yield Label("[bold]Add Event[/]", id="cd_form_title")
            yield Label("Event Name")
            yield Input(placeholder="e.g. Mom's Birthday...", id="cd_event_name")
            yield Label("Date")
            yield Input(
                placeholder="YYYY-MM-DD",
                value=date.today().strftime("%Y-%m-%d"),
                id="cd_event_date"
            )
            with Horizontal(id="cd_form_buttons"):
                yield Button("Save", variant="primary", id="cd_save")
            yield Label("Press Escape to close", id="cd_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cd_save":
            self._try_save()

    def on_input_submitted(self, event: Input.Submitted):
        self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)

    def _try_save(self):
        name = self.query_one("#cd_event_name", Input).value.strip()
        date_str = self.query_one("#cd_event_date", Input).value.strip()
        if not name:
            self.notify("Event name is required.", severity="error")
            return
        if not date_str:
            self.notify("Date is required.", severity="error")
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.notify("Invalid date. Use YYYY-MM-DD format.", severity="error")
            return
        self.dismiss({"name": name.title(), "date": date_str})


class DeleteConfirmModal(ModalScreen):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def compose(self) -> ComposeResult:
        with Container(id="cd_del_container"):
            yield Label(f'Delete "[bold]{self._name}[/]"?', id="cd_del_label")
            with Horizontal(id="cd_del_buttons"):
                yield Button("Delete", variant="error", id="cd_del_confirm")
            yield Label("Press Escape to close", id="cd_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cd_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


class CountdownWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("n", "add", "Add Event"),
        Binding("d", "delete", "Delete Event"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="cd_container"):
            yield Label("[bold]Countdown Tracker[/]", id="cd_main_title")

            with Horizontal(id="cd_action_row"):
                yield Button("Add Event", variant="primary", id="cd_add_btn")
                yield Button("Delete Event", variant="error", id="cd_del_btn")

            with Horizontal(id="cd_display_row"):
                # Left: scrollable list of ALL events, sorted by soonest
                with Vertical(id="cd_left_panel"):
                    yield Label("All Events", id="cd_left_heading")
                    yield VerticalScroll(id="cd_event_list")
                # Right: compact reference table (event + date only)
                with Vertical(id="cd_right_panel"):
                    yield Label("Overview", id="cd_right_heading")
                    yield DataTable(id="cd_ref_table")

    def on_mount(self):
        init_db()

        t2 = self.query_one("#cd_ref_table", DataTable)
        t2.add_columns("Event", "Date")
        t2.cursor_type = "row"

        self._refresh_all()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "cd_add_btn":
            self.action_add()
        elif pid == "cd_del_btn":
            self.action_delete()

    def action_add(self):
        self.app.push_screen(EventFormModal(), self._on_add)

    def action_delete(self):
        # Use the ref table cursor since both are synced
        table = self.query_one("#cd_ref_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            event_id = int(row_key)
            for e in get_events():
                if e["id"] == event_id:
                    self.app.push_screen(
                        DeleteConfirmModal(e["name"].title()),
                        lambda confirmed: self._on_delete(event_id, confirmed)
                    )
                    return
        except (IndexError, ValueError):
            pass

    def _on_add(self, data):
        if data:
            add_event(data["name"], data["date"])
            self._refresh_all()

    def _on_delete(self, event_id, confirmed):
        if confirmed:
            delete_event(event_id)
            self._refresh_all()

    def _refresh_all(self):
        self.call_after_refresh(self._refresh_left)
        self._refresh_right()

    async def _refresh_left(self):
        scroll = self.query_one("#cd_event_list", VerticalScroll)
        await scroll.remove_children()

        events = sorted(get_events(), key=lambda e: e["target_date"])
        has_cards = False
        for e in events:
            diff, label = days_until(e["target_date"])

            if label == "today":
                day_val = "0"
                day_classes = "cd_card_days"
                suffix = "[bold]Today![/]"
            elif label == "days ago":
                day_val = f"-{diff}"
                day_classes = "cd_card_days cd_card_days_past"
                suffix = f"[dim]{diff}d ago[/]"
            else:
                day_val = str(diff)
                day_classes = "cd_card_days"
                suffix = f"[dim]days left[/]"

            card = Horizontal(classes="cd_event_card")
            has_cards = True
            await scroll.mount(card)
            await card.mount(
                Digits(day_val, classes=day_classes),
                Vertical(
                    Label(f"[bold]{e['name'].title()}[/]", classes="cd_card_name"),
                    Label(suffix, classes="cd_card_suffix"),
                    classes="cd_card_info",
                ),
            )

        if not has_cards:
            await scroll.mount(Label("[dim]No events yet. Press n to add one.[/]", id="cd_empty"))

    def _refresh_right(self):
        table = self.query_one("#cd_ref_table", DataTable)
        table.clear()
        events = sorted(get_events(), key=lambda e: e["target_date"])
        for e in events:
            table.add_row(e["name"].title(), e["target_date"], key=str(e["id"]))


class CountdownTab(TabPane):
    def compose(self) -> ComposeResult:
        yield CountdownWidget()
