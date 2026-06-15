"""Calorie Budgeter — main widget and tab wrapper."""

from datetime import date, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, TabPane

from .db import (
    add_log,
    calculate_targets,
    delete_log,
    get_dynamic_daily_target,
    get_profile,
    get_today_total,
    get_week_logs,
    get_week_total,
    init_db,
    save_profile,
)
from .modals import DeleteLogModal, ProfileSetupModal

# ── Helpers ──────────────────────────────────────────────────────────────────


def _bar(consumed: int, budget: int, width: int = 28) -> str:
    """Return a Rich-markup progress bar string."""
    if budget <= 0:
        return "[dim]" + "─" * width + "[/]"
    pct = min(consumed / budget, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    if pct >= 1.0:
        color = "#ff5252"
    elif pct >= 0.85:
        color = "#ffd740"
    else:
        color = "#69f0ae"
    return f"[{color}]{bar}[/] {pct:.0%}"


def _fmt(n: int) -> str:
    return f"{n:,}"


# ═══════════════════════════════════════════════════════════════════════════
# Main Widget
# ═══════════════════════════════════════════════════════════════════════════


class CalorieWidget(Widget, can_focus=True):
    BINDINGS = [
        Binding("n", "log_meal", "Log Meal"),
        Binding("d", "delete_entry", "Delete Entry"),
        Binding("s", "setup_profile", "Setup Profile"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="cb_root"):
            yield Label("[bold]Calorie Budgeter[/]", id="cb_title")

            # ── Stats row ──────────────────────────────────────────────────
            with Horizontal(id="cb_stats_row"):
                with Container(id="cb_weekly_panel"):
                    yield Label("[bold]This Week[/]", id="cb_weekly_heading")
                    yield Label("", id="cb_weekly_budget")
                    yield Label("", id="cb_weekly_eaten")
                    yield Label("", id="cb_weekly_left")
                    yield Label("", id="cb_weekly_bar")

                with Container(id="cb_today_panel"):
                    yield Label("[bold]Today[/]", id="cb_today_heading")
                    yield Label("", id="cb_today_target")
                    yield Label("", id="cb_today_eaten")
                    yield Label("", id="cb_today_left")
                    yield Label("", id="cb_today_bar")

            # ── Log table ─────────────────────────────────────────────────
            with Horizontal(id="cb_table_header"):
                yield Label("[bold]Today's Log[/]", id="cb_log_label")
                yield Button("Setup Profile", id="cb_setup_btn")

            yield DataTable(id="cb_table")

            # ── Input row ─────────────────────────────────────────────────
            with Horizontal(id="cb_input_row"):
                yield Input(placeholder="Meal / food name...", id="cb_label_input")
                yield Input(placeholder="kcal", id="cb_cal_input")
                yield Button("Log", variant="primary", id="cb_log_btn")
                yield Button("Delete", variant="error", id="cb_del_btn")

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        init_db()
        table = self.query_one("#cb_table", DataTable)
        table.add_columns("Day / Meal", "kcal")
        table.cursor_type = "row"
        table.tooltip = "n: Log  d: Delete  s: Profile Setup"
        self._refresh_all()

    # ── Button dispatch ───────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pid = event.button.id
        if pid == "cb_log_btn":
            self.action_log_meal()
        elif pid == "cb_del_btn":
            self.action_delete_entry()
        elif pid == "cb_setup_btn":
            self.action_setup_profile()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("cb_label_input", "cb_cal_input"):
            self.action_log_meal()

    # ── Actions ───────────────────────────────────────────────────────────

    def action_log_meal(self) -> None:
        label_inp = self.query_one("#cb_label_input", Input)
        cal_inp = self.query_one("#cb_cal_input", Input)
        label = label_inp.value.strip()
        cal_str = cal_inp.value.strip()

        if not label:
            self.notify("Enter a meal name.", severity="error")
            return
        if not cal_str.isdigit() or int(cal_str) <= 0:
            self.notify("Enter a positive calorie amount.", severity="error")
            return

        add_log(label, int(cal_str))
        label_inp.value = ""
        cal_inp.value = ""
        self._refresh_all()

    def action_delete_entry(self) -> None:
        table = self.query_one("#cb_table", DataTable)
        if table.row_count == 0:
            self.notify("Nothing to delete.", severity="warning")
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
        except IndexError:
            return

        # Only entry_ rows are real log entries
        if not row_key.startswith("entry_"):
            self.notify("Select a meal row to delete.", severity="warning")
            return

        entry_id = int(row_key[len("entry_") :])
        logs = get_week_logs()
        entry = next((e for e in logs if e["id"] == entry_id), None)
        if entry is None:
            return

        self.app.push_screen(
            DeleteLogModal(entry["label"], entry["calories"]),
            lambda confirmed: self._on_entry_deleted(entry_id, confirmed),
        )

    def _on_entry_deleted(self, entry_id: int, confirmed: bool) -> None:
        if confirmed:
            delete_log(entry_id)
            self._refresh_all()

    def action_setup_profile(self) -> None:
        self.app.push_screen(
            ProfileSetupModal(get_profile()),
            self._on_profile_saved,
        )

    def _on_profile_saved(self, data: dict | None) -> None:
        if data is None:
            return
        save_profile(
            data["weight"],
            data["height"],
            data["age"],
            data["gender"],
            data["activity"],
            data["goal_kg_per_week"],
        )
        self._refresh_all()
        self.notify("Profile saved!", severity="information")

    # ── Refresh ───────────────────────────────────────────────────────────

    def _refresh_all(self) -> None:
        self._refresh_stats()
        self._refresh_table()

    def _refresh_stats(self) -> None:
        profile = get_profile()

        if profile is None:
            no_profile = "[dim]Set up your profile to see your budgets (press s)[/]"
            for wid in (
                "#cb_weekly_budget",
                "#cb_weekly_eaten",
                "#cb_weekly_left",
                "#cb_weekly_bar",
                "#cb_today_target",
                "#cb_today_eaten",
                "#cb_today_left",
                "#cb_today_bar",
            ):
                self.query_one(wid, Label).update("")
            self.query_one("#cb_weekly_budget", Label).update(no_profile)
            return

        weekly_budget, daily_base, tdee = calculate_targets(profile)
        week_eaten = get_week_total()
        week_left = weekly_budget - week_eaten
        today_eaten = get_today_total()
        today_target = get_dynamic_daily_target(weekly_budget)
        today_left = today_target - today_eaten

        # Weekly panel
        self.query_one("#cb_weekly_budget", Label).update(
            f"Budget:    [bold]{_fmt(weekly_budget)}[/] kcal"
        )
        self.query_one("#cb_weekly_eaten", Label).update(
            f"Eaten:     [bold]{_fmt(week_eaten)}[/] kcal"
        )
        left_color = "#ff5252" if week_left < 0 else "#69f0ae"
        self.query_one("#cb_weekly_left", Label).update(
            f"Remaining: [bold {left_color}]{_fmt(week_left)}[/] kcal"
        )
        self.query_one("#cb_weekly_bar", Label).update(_bar(week_eaten, weekly_budget))

        # Today panel
        self.query_one("#cb_today_target", Label).update(
            f"Target:    [bold]{_fmt(today_target)}[/] kcal"
        )
        self.query_one("#cb_today_eaten", Label).update(
            f"Eaten:     [bold]{_fmt(today_eaten)}[/] kcal"
        )
        left_color_today = "#ff5252" if today_left < 0 else "#69f0ae"
        self.query_one("#cb_today_left", Label).update(
            f"Remaining: [bold {left_color_today}]{_fmt(today_left)}[/] kcal"
        )
        self.query_one("#cb_today_bar", Label).update(_bar(today_eaten, today_target))

    def _refresh_table(self) -> None:
        table = self.query_one("#cb_table", DataTable)
        table.clear()

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Group entries by date
        all_logs = get_week_logs()
        by_date: dict[str, list] = {}
        for entry in all_logs:
            by_date.setdefault(entry["date"], []).append(entry)

        for i in range(7):
            day = week_start + timedelta(days=i)
            if day > today:
                break  # don't show future days

            day_str = day.isoformat()
            is_today = day == today
            day_label = day.strftime("%A, %b %d") + ("  (today)" if is_today else "")
            entries = by_date.get(day_str, [])
            day_total = sum(e["calories"] for e in entries)
            color = "#ffd740" if is_today else "#7eb8f7"

            # Day header row
            table.add_row(
                f"[bold {color}]{day_label}[/]",
                f"[bold {color}]{_fmt(day_total)} kcal[/]"
                if entries
                else f"[dim {color}]—[/]",
                key=f"day_{day_str}",
            )

            # Meal rows
            if entries:
                for entry in entries:
                    table.add_row(
                        f"  {entry['label']}",
                        f"  {_fmt(entry['calories'])}",
                        key=f"entry_{entry['id']}",
                    )
            else:
                table.add_row(
                    "  [dim]No entries[/]",
                    "",
                    key=f"empty_{day_str}",
                )


# ═══════════════════════════════════════════════════════════════════════════
# Tab Wrapper
# ═══════════════════════════════════════════════════════════════════════════


class CalorieBudgeterTab(TabPane):
    def compose(self) -> ComposeResult:
        yield CalorieWidget()
