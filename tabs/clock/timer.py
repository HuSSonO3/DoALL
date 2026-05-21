from textual.app import ComposeResult, RenderResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label, Static, TabbedContent , TabPane, Button, DataTable, Digits
from textual.widget import Widget
from textual.containers import Container, Horizontal, VerticalScroll, ItemGrid, Grid
from textual.reactive import reactive
from textual.binding import Binding
import time
from textual import events

class TimerWidget(Widget, can_focus=True):
    # BINDINGS = [
    #         Binding("k", "change_count(1)", "Increment"),  
    #         Binding("j", "change_count(-1)", "Decrement"),
    #     ]
        
    def compose(self) -> ComposeResult:
        yield Grid( 
            Container(
                HoldButton("+", id="timer_button_add1", classes="timer_hours_before"),
                Container(Digits("00",id="timer_hours_before"), Label(":",id="timer_label"), classes="timer_digit_container"),
                HoldButton("-", id="timer_button_minus1", classes="timer_hours_before"),
            id="timer_overall_container"),
            Container(
                HoldButton("+", id="timer_button_add2", classes="timer_minutes_before"),
                Container(Digits("00",id="timer_minutes_before"), Label(":", id="timer_label2"), classes="timer_digit_container"),
                HoldButton("-", id="timer_button_minus2", classes="timer_minutes_before"),
            id="timer_overall_container2"),
            Container(
                HoldButton("+", id="timer_button_add3", classes="timer_seconds_before"),
                Container(Digits("00",id="timer_seconds_before"), classes="timer_digit_container"),
                HoldButton("-", id="timer_button_minus3", classes="timer_seconds_before"),
            id="timer_overall_container3"),
        id="timer_first_container")

        yield Container(Button("Start", id="timer_start"), id="timer_start_container")

        yield Grid(
            Grid(
                Container(Digits("00",id="timer_hours_after"), Label(":",id="timer_label"), classes="timer_digit_container"),
                Container(Digits("00",id="timer_minutes_after"), Label(":", id="timer_label2"), classes="timer_digit_container"),
                Container(Digits("00",id="timer_seconds_after"), classes="timer_digit_container"), id="timer_grid_after"
            ),
            Container(Button("Pause", id="timer_pause"), id="timer_pause_container"),
            Grid(
                Button("Cancel", id="timer_cancel"),
                Button("Resume", id="timer_resume"),
                Button("Restart", id="timer_restart") 
            
            ,id="timer_buttons_container"),
            id="timer_second_container")


    def on_mount(self) -> None:
        self.second_container = self.query_one("#timer_second_container", Grid)
        self.first_container = self.query_one("#timer_first_container", Grid)
        self.pause_container = self.query_one("#timer_pause_container", Container)        
        self.buttons_container = self.query_one("#timer_buttons_container", Grid)
        self.start_container = self.query_one("#timer_start_container", Container)        

        self.second_container.styles.display = 'none'
        self.pause_container.styles.display = 'none'
        self.buttons_container.styles.display = 'none'

        self.before1 = self.query_one("#timer_hours_before", Digits)
        self.before2 = self.query_one("#timer_minutes_before", Digits)
        self.before3 = self.query_one("#timer_seconds_before", Digits)

        self.after1 = self.query_one("#timer_hours_after", Digits)
        self.after2 = self.query_one("#timer_minutes_after", Digits)
        self.after3 = self.query_one("#timer_seconds_after", Digits)

    def on_button_pressed(self, event:Button.Pressed) -> None:
        button_id = event.button.id
        button_classes = event.button.classes
        button_label = event.button.label

    def buttons_logic(self, button_id, button_classes):
        match button_id:
            case s if "add" in s:
                self.change_timer(button_classes, "add")
            case s if "minus" in s:
                self.change_timer(button_classes, "minus")
            case 'timer_start':
                self.start_timer()
            case 'timer_pause':
                self.pause_timer()
            case 'timer_resume':
                self.resume_timer()
            case 'timer_cancel':
                self.cancel_timer()
            case 'timer_restart':
                self.restart_timer()


    def change_timer(self, button_classes, operation):
        items_to_check = {'-active', '-style-default'}
        digits = button_classes - items_to_check
        digit = next(iter(digits))
        queried_digit = self.query_one(f"#{digit}", Digits)
        
        module = 60

        if digit == 'timer_hours_before':
            module = 100

        if operation == 'add':
            new_value = (int(queried_digit.value) + 1) % module

        else:
            new_value = (int(queried_digit.value) - 1) % module

        queried_digit.update(f"{new_value:02d}")
        self.log(queried_digit.value)

    def start_timer(self):
        # Prolly having one digit instead of 6 would have been easier but alas.

        self.timer_in_seconds = (int(self.before1.value) * 3600) + (int(self.before2.value) * 60) + int(self.before3.value)

        self.first_container.styles.display = 'none'
        self.start_container.styles.display = 'none'
        self.second_container.styles.display = 'block'

        self.total_seconds = self.timer_in_seconds

        hours, remainder = divmod(self.total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.after1.update(f"{hours:02d}")
        self.after2.update(f"{minutes:02d}")
        self.after3.update(f"{seconds:02d}")

        self.my_timer = self.set_interval(1, self.increase_timer)

        self.pause_container.styles.display = 'block'
        self.buttons_container.styles.display = 'none'

    def increase_timer(self):
        self.total_seconds -= 1
        
        hours, remainder = divmod(self.total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.after1.update(f"{hours:02d}")
        self.after2.update(f"{minutes:02d}")
        self.after3.update(f"{seconds:02d}")

        if self.total_seconds == 0:
            self.my_timer.pause()
            self.app.bell() # add better sound later using a lib or smth
            self.notify("Alarm is Done!!")
            self.start_container.styles.display = 'block'
            self.pause_container.styles.display = 'none'
            self.first_container.styles.display = 'block'
            self.second_container.styles.display = 'none'
            

    def pause_timer(self):
        self.my_timer.pause()
        self.pause_container.styles.display = 'none'
        self.buttons_container.styles.display = 'block'

    def resume_timer(self):
        self.my_timer.resume()
        self.pause_container.styles.display = 'block'
        self.buttons_container.styles.display = 'none'

    def restart_timer(self):
        self.total_seconds = self.timer_in_seconds

        hours, remainder = divmod(self.total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.after1.update(f"{hours:02d}")
        self.after2.update(f"{minutes:02d}")
        self.after3.update(f"{seconds:02d}")

    def cancel_timer(self):
        self.my_timer.stop()
        self.timer_in_seconds = 0
        self.total_seconds = 0
        self.pause_container.styles.display = 'none'
        self.buttons_container.styles.display = 'none'
        self.first_container.styles.display = 'block'
        self.second_container.styles.display = 'none'
        self.start_container.styles.display = 'block'


class HoldButton(Button):
    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.button_id = self.id
        self.button_classes = self.classes
        self.hold_timer = self.set_timer(0.5, lambda: self.start_hold(self.button_id, self.button_classes))

    def start_hold(self, button_id, button_classes) -> None:
        self.hold_timer = self.set_interval(0.1, lambda: self.parent.parent.parent.buttons_logic(button_id, button_classes))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.stop_timer()

    def on_leave(self, event: events.Leave) -> None:
        self.stop_timer()

    def stop_timer(self) -> None:
        if hasattr(self, 'hold_timer'):
            self.hold_timer.stop()