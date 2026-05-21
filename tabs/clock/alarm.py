from textual.app import ComposeResult, RenderResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Footer, Placeholder, TabPane, Label, Static, TabbedContent , TabPane, Button, DataTable, Digits,SelectionList, Input
from textual import events
from textual.widget import Widget
from textual.containers import Container, Horizontal, VerticalScroll, ItemGrid, Grid
from textual.reactive import reactive
from textual.binding import Binding
import datetime

import sqlite3

class AlarmWidget(Widget):
    def compose(self) -> ComposeResult:
        yield Container(
            Label("Hello ! Add Alarms?"),
            Button("Add", id="alarm_add"),
        id="alarm_first_container"
        )

    def on_button_pressed(self, event:Button.Pressed):
        button_id = event.button.id
        if button_id == 'alarm_add':
            self.app.push_screen(AlarmAddModal())

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
                Container(Digits("00",id="alarm_hours_add"), Label(":"), classes="alarm_digit_add_container"),
                HoldButton("-", id="alarm_button_minus", classes="alarm_hours_add"),
            id="alarm_add_container"),
            Container(
                HoldButton("+", id="alarm_button_add2", classes="alarm_minutes_add"),
                Container(Digits("00",id="alarm_minutes_add"), classes="alarm_digit_add_container"),
                HoldButton("-", id="alarm_button_minus2", classes="alarm_minutes_add"),
            id="alarm_add_container2"),id="alarm_add_grid"),
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
        self.add_details_container = self.query_one("#alarm_add_details_container", Container)
        self.days_selected_input = self.query_one("#alarm_selection_options", SelectionList)
        self.alarm_name_input = self.query_one("#alarm_add_name", Input)

        today = datetime.datetime.now()
        self.days_selected_input.select(self.day_to_value[today.strftime("%A")])

    def on_button_pressed(self, event:Button.Pressed) -> None:
        button_id = event.button.id
        button_classes = event.button.classes
        self.buttons_logic(button_id,button_classes)
        

    def buttons_logic(self, button_id, button_classes):
        match button_id:
            case s if "add" in s and not "alarm_added_selection":
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

        self.log(queried_digit)
        
        module = 60

        if digit == 'alarm_hours_add':
            module = 24

        if operation == 'add':
            new_value = (int(queried_digit.value) + 1) % module

        else:
            new_value = (int(queried_digit.value) - 1) % module

        queried_digit.update(f"{new_value:02d}")
        self.log(queried_digit.value)

    def add_new_alarm(self):
        self.log(self.days_selected_input.selected)
        data = {'name': 'Alarm', 'days': ''}
        
        if not self.days_selected_input.selected:
            today = datetime.datetime.now()
            self.days_selected_input.select(self.day_to_value[today.strftime("%A")])

        selected_days = self.days_selected_input.selected
        data['days'] = selected_days

        if self.alarm_name_input.value:
            data['name'] = self.alarm_name_input.value

        self.log(data)



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
