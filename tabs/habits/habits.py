"""Habit Tracker — widget and tab wrapper."""

from datetime import datetime, timedelta

from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Input, Label, TabPane
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from .db import (
    init_db, add_habit, get_habits, update_habit, delete_habit,
    toggle_entry, get_week_entries, get_streak, get_completion_rate,
)
from .modals import HabitFormModal, HabitDeleteConfirmModal


# ═══════════════════════════════════════════════════════════════
# Main Widget
# ═══════════════════════════════════════════════════════════════

class HabitWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("n", "add_habit", "Add Habit"),
        Binding("e", "edit_habit", "Edit Habit"),
        Binding("d", "delete_habit", "Delete Habit"),
        Binding("space", "toggle_today", "Toggle Today"),
        Binding("left", "prev_week", "Previous Week"),
        Binding("right", "next_week", "Next Week"),
    ]

    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._week_start = self._this_monday()

    @staticmethod
    def _this_monday():
        today = datetime.now()
        return today - timedelta(days=today.weekday())

    def compose(self) -> ComposeResult:
        with Vertical(id="habit_container"):
            # ── Title ──
            yield Label("[bold]Habit Tracker[/]", id="habit_title")

            # ── Add habit row ──
            with Horizontal(id="habit_input_row"):
                yield Input(placeholder="New habit name...", id="habit_name_input")
                yield Button("Add", variant="primary", id="habit_add_btn")

            # ── Week navigation ──
            with Horizontal(id="habit_week_nav"):
                yield Button("◀  Prev", id="habit_prev_btn")
                yield Label(self._week_label(), id="habit_week_label")
                yield Button("Next  ▶", id="habit_next_btn")

            # ── Weekly grid ──
            yield DataTable(id="habit_table")

            # ── Bottom bar ──
            with Horizontal(id="habit_bottom_row"):
                yield Label("", id="habit_stats")
                yield Button("Edit Habit", id="habit_edit_btn")
                yield Button("Delete Habit", variant="error", id="habit_delete_btn")

    def on_mount(self):
        init_db()
        table = self.query_one("#habit_table", DataTable)
        table.add_columns("Habit", "Streak", *self.DAY_NAMES)
        table.cursor_type = "row"
        table.tooltip = (
            "Space: Toggle Today  n: Add  e: Edit  d: Delete  ←/→: Week"
        )
        self._refresh_all()

    # ── Week helpers ──

    def _week_label(self):
        end = self._week_start + timedelta(days=6)
        if self._week_start.month != end.month:
            return f"{self._week_start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
        return f"{self._week_start.strftime('%b %d')} – {end.strftime('%d, %Y')}"

    def _week_date_strs(self):
        return [
            (self._week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(7)
        ]

    # ── Navigation ──

    def action_prev_week(self):
        self._week_start -= timedelta(days=7)
        self._refresh_all()

    def action_next_week(self):
        self._week_start += timedelta(days=7)
        self._refresh_all()

    # ── Button dispatch ──

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "habit_add_btn":
            self.action_add_habit()
        elif pid == "habit_prev_btn":
            self.action_prev_week()
        elif pid == "habit_next_btn":
            self.action_next_week()
        elif pid == "habit_edit_btn":
            self.action_edit_habit()
        elif pid == "habit_delete_btn":
            self.action_delete_habit()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "habit_name_input":
            self.action_add_habit()

    # ── Actions ──

    def action_add_habit(self):
        inp = self.query_one("#habit_name_input", Input)
        name = inp.value.strip()
        if not name:
            self.app.push_screen(HabitFormModal(), self._on_habit_saved)
        else:
            result = add_habit(name)
            if result is None:
                self.notify(f'"{name}" already exists.', severity="error")
            else:
                inp.value = ""
                self._refresh_all()

    def _on_habit_saved(self, name):
        if name is None:
            return
        result = add_habit(name)
        if result is None:
            self.notify(f'"{name}" already exists.', severity="error")
        else:
            self._refresh_all()

    def action_edit_habit(self):
        habit = self._get_selected_habit()
        if habit is None:
            return
        self.app.push_screen(
            HabitFormModal(habit["name"]),
            lambda new_name: self._on_habit_edited(habit["id"], new_name)
        )

    def _on_habit_edited(self, habit_id, new_name):
        if new_name is None:
            return
        if not update_habit(habit_id, new_name):
            self.notify(f'"{new_name}" already exists.', severity="error")
        self._refresh_all()

    def action_delete_habit(self):
        habit = self._get_selected_habit()
        if habit is None:
            return
        self.app.push_screen(
            HabitDeleteConfirmModal(habit["name"]),
            lambda confirmed: self._on_habit_deleted(habit["id"], confirmed)
        )

    def _on_habit_deleted(self, habit_id, confirmed):
        if confirmed:
            delete_habit(habit_id)
            self._refresh_all()

    def action_toggle_today(self):
        habit = self._get_selected_habit()
        if habit is None:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        now_done = toggle_entry(habit["id"], today)
        self._refresh_all()
        status = "done" if now_done else "undone"
        self.notify(f'"{habit["name"]}" marked {status} for today.')

    # ── Selection helper ──

    def _get_selected_habit(self):
        table = self.query_one("#habit_table", DataTable)
        if table.row_count == 0:
            self.notify("No habits yet. Add one first.", severity="warning")
            return None
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            habit_id = int(row_key)
            for h in get_habits():
                if h["id"] == habit_id:
                    return dict(h)
        except (IndexError, ValueError):
            pass
        return None

    # ── Refresh ──

    def _refresh_all(self):
        self._refresh_week_label()
        self._refresh_table()
        self._refresh_stats()

    def _refresh_week_label(self):
        self.query_one("#habit_week_label", Label).update(self._week_label())

    def _refresh_table(self):
        table = self.query_one("#habit_table", DataTable)
        table.clear()
        habits = get_habits()
        dates = self._week_date_strs()
        today_str = datetime.now().strftime("%Y-%m-%d")

        for h in habits:
            week = get_week_entries(h["id"], dates[0])
            streak, _longest = get_streak(h["id"], today_str)
            streak_str = f"{streak}d"

            row = [h["name"], streak_str]
            for d in dates:
                if week[d]:
                    row.append("[bold #4caf50]✓[/]")
                else:
                    row.append("[dim]·[/]")
            table.add_row(*row, key=str(h["id"]))

    def _refresh_stats(self):
        habits = get_habits()
        n = len(habits)
        if n == 0:
            self.query_one("#habit_stats", Label).update("[dim]No habits yet[/]")
            return
        total_rate = sum(get_completion_rate(h["id"]) for h in habits) / n
        self.query_one("#habit_stats", Label).update(
            f"[dim]{n} habit{'s' if n != 1 else ''}  •  "
            f"{total_rate:.0%} overall completion[/]"
        )


# ═══════════════════════════════════════════════════════════════
# Tab Wrapper
# ═══════════════════════════════════════════════════════════════

class HabitTab(TabPane):
    def compose(self) -> ComposeResult:
        yield HabitWidget()
