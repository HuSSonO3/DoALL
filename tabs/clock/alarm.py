from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Digits, Input, Label, SelectionList
from textual.widget import Widget
from textual.containers import Container, Grid
from textual import events
from textual.binding import Binding
import datetime
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Alarm',
            hour INTEGER NOT NULL,
            minute INTEGER NOT NULL,
            days TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


class AlarmWidget(Widget, can_focus=True):
    BINDINGS = [
        Binding("d", "delete_alarm", "Delete"),
        Binding("t", "toggle_alarm", "Toggle On/Off"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            DataTable(id="alarm_table"),
            Button("Add", id="alarm_add"),
            id="alarm_first_container"
        )

    def on_mount(self):
        init_db()
        self.ringing_alarms = set()
        self.last_minute_checked = None

        table = self.query_one("#alarm_table", DataTable)
        table.add_columns("Name", "Time", "Days", "Status")
        table.cursor_type = "row"
        self.refresh_alarm_table()

        self.ring_check = self.set_interval(1, self.check_alarms)

    def refresh_alarm_table(self):
        table = self.query_one("#alarm_table", DataTable)
        table.clear()
        conn = get_db()
        rows = conn.execute("SELECT * FROM alarms ORDER BY hour, minute").fetchall()
        conn.close()

        day_names = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
        for row in rows:
            time_str = f"{row['hour']:02d}:{row['minute']:02d}"
            days_str = ""
            if row['days']:
                day_nums = [int(d) for d in row['days'].split(",") if d]
                days_str = ", ".join(day_names[d] for d in day_nums)
            status = "ON" if row['enabled'] else "OFF"
            table.add_row(row['name'], time_str, days_str, status, key=str(row['id']))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'alarm_add':
            self.app.push_screen(AlarmAddModal(), self.on_alarm_added)

    def on_alarm_added(self, result):
        if result:
            self.refresh_alarm_table()

    def _get_selected_alarm_id(self):
        table = self.query_one("#alarm_table", DataTable)
        if table.row_count == 0:
            return None
        row_index = table.cursor_row
        try:
            row_key = table.ordered_rows[row_index]
        except IndexError:
            return None
        return row_key.key.value

    def action_delete_alarm(self):
        alarm_id = self._get_selected_alarm_id()
        if alarm_id is not None:
            conn = get_db()
            conn.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
            conn.commit()
            conn.close()
            self.refresh_alarm_table()

    def action_toggle_alarm(self):
        alarm_id = self._get_selected_alarm_id()
        self.log(alarm_id)
        self.log("Hi")
        if alarm_id is not None:
            conn = get_db()
            row = conn.execute("SELECT enabled FROM alarms WHERE id = ?", (alarm_id,)).fetchone()
            if row:
                new_state = 0 if row['enabled'] else 1
                conn.execute("UPDATE alarms SET enabled = ? WHERE id = ?", (new_state, alarm_id))
                conn.commit()
            conn.close()
            self.refresh_alarm_table()

    def check_alarms(self):
        now = datetime.datetime.now()
        minute_key = (now.hour, now.minute)

        if self.last_minute_checked != minute_key:
            self.ringing_alarms.clear()
            self.last_minute_checked = minute_key

        today_day = (now.weekday() + 2) % 7

        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM alarms WHERE enabled = 1 AND hour = ? AND minute = ?",
            (now.hour, now.minute)
        ).fetchall()
        conn.close()

        for row in rows:
            alarm_id = row['id']
            if alarm_id in self.ringing_alarms:
                continue

            if row['days']:
                alarm_days = [int(d) for d in row['days'].split(",") if d]
                if today_day not in alarm_days:
                    continue

            self.ringing_alarms.add(alarm_id)
            self.app.bell()
            self.notify(f"Alarm: {row['name']} - {row['hour']:02d}:{row['minute']:02d}")
            self.app.push_screen(AlarmRingModal(row['name'], row['hour'], row['minute']))


class AlarmRingModal(ModalScreen):
    def __init__(self, name, hour, minute):
        super().__init__()
        self.alarm_name = name
        self.alarm_hour = hour
        self.alarm_minute = minute

    def compose(self):
        yield Container(
            Label(f"⏰ {self.alarm_name}", id="ring_title"),
            Label(f"{self.alarm_hour:02d}:{self.alarm_minute:02d}", id="ring_time"),
            Button("Dismiss", id="ring_dismiss"),
            id="alarm_ring_container"
        )

    def on_mount(self):
        self.ring_timer = self.set_interval(2, lambda: self.app.bell())

    def on_button_pressed(self, event):
        if event.button.id == "ring_dismiss":
            self.ring_timer.stop()
            self.dismiss(None)

    def on_key(self, event):
        if event.key == "escape":
            self.ring_timer.stop()
            self.dismiss(None)


class AlarmAddModal(ModalScreen):
    repeat_options = [
        ("Saturday", 0),
        ("Sunday", 1),
        ("Monday", 2),
        ("Tuesday", 3),
        ("Wednesday", 4),
        ("Thursday", 5),
        ("Friday", 6),
    ]

    day_to_value = {
        "Saturday": 0, "Sunday": 1, "Monday": 2, "Tuesday": 3,
        "Wednesday": 4, "Thursday": 5, "Friday": 6
    }

    def compose(self) -> ComposeResult:
        yield Container(
            Grid(
                Container(
                    HoldButton("+", id="alarm_button_add", classes="alarm_hours_add"),
                    Container(Digits("00", id="alarm_hours_add"), Label(":"), classes="alarm_digit_add_container"),
                    HoldButton("-", id="alarm_button_minus", classes="alarm_hours_add"),
                    id="alarm_add_container"),
                Container(
                    HoldButton("+", id="alarm_button_add2", classes="alarm_minutes_add"),
                    Container(Digits("00", id="alarm_minutes_add"), classes="alarm_digit_add_container"),
                    HoldButton("-", id="alarm_button_minus2", classes="alarm_minutes_add"),
                    id="alarm_add_container2"),
                id="alarm_add_grid"),
            Container(
                Container(Label("Name"), Input(placeholder="Alarm Name", id="alarm_add_name")),
                Container(
                    Label("Repeat"),
                    Button("Select days ▼", id="alarm_selection_toggle"),
                    id="alarm_repeat_header"
                ),
                SelectionList(*self.repeat_options, id="alarm_selection_options"),
                id="alarm_add_details_container"),
            Container(Button("Add", id="alarm_added_selection"), id="alarm_added_selection_container"),
            id="alarm_add_modal_container")

    def on_mount(self):
        self.options = self.query_one("#alarm_selection_options", SelectionList)
        self.options.display = False
        self.days_selected_input = self.query_one("#alarm_selection_options", SelectionList)
        self.alarm_name_input = self.query_one("#alarm_add_name", Input)
        self.hours_digits = self.query_one("#alarm_hours_add", Digits)
        self.minutes_digits = self.query_one("#alarm_minutes_add", Digits)

        today = datetime.datetime.now()
        self.days_selected_input.select(self.day_to_value[today.strftime("%A")])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        button_classes = event.button.classes
        self.buttons_logic(button_id, button_classes)

    def buttons_logic(self, button_id, button_classes):
        match button_id:
            case s if "add" in s and s != "alarm_added_selection":
                self.change_timer(button_classes, "add")
            case s if "minus" in s:
                self.change_timer(button_classes, "minus")
            case 'alarm_selection_toggle':
                self.options.display = not self.options.display
            case 'alarm_added_selection':
                self.add_new_alarm()

    def change_timer(self, button_classes, operation):
        items_to_check = {'-active', '-style-default'}
        digits = button_classes - items_to_check
        digit = next(iter(digits))
        queried_digit = self.query_one(f"#{digit}", Digits)

        module = 60
        if digit == 'alarm_hours_add':
            module = 24

        if operation == 'add':
            new_value = (int(queried_digit.value) + 1) % module
        else:
            new_value = (int(queried_digit.value) - 1) % module

        queried_digit.update(f"{new_value:02d}")

    def add_new_alarm(self):
        if not self.days_selected_input.selected:
            today = datetime.datetime.now()
            self.days_selected_input.select(self.day_to_value[today.strftime("%A")])

        selected_days = self.days_selected_input.selected
        days_str = ",".join(str(d) for d in selected_days)

        name = self.alarm_name_input.value or "Alarm"
        hour = int(self.hours_digits.value)
        minute = int(self.minutes_digits.value)

        conn = get_db()
        conn.execute(
            "INSERT INTO alarms (name, hour, minute, days) VALUES (?, ?, ?, ?)",
            (name, hour, minute, days_str)
        )
        conn.commit()
        conn.close()

        self.dismiss(True)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class HoldButton(Button):
    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.button_id = self.id
        self.button_classes = self.classes
        self.hold_timer = self.set_timer(0.5, lambda: self.start_hold(self.button_id, self.button_classes))

    def start_hold(self, button_id, button_classes) -> None:
        self.hold_timer = self.set_interval(0.1, lambda: self.app.screen.buttons_logic(button_id, button_classes))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.stop_timer()

    def on_leave(self, event: events.Leave) -> None:
        self.stop_timer()

    def stop_timer(self) -> None:
        if hasattr(self, 'hold_timer'):
            self.hold_timer.stop()
