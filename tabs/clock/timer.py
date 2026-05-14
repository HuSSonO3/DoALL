from textual.app import ComposeResult, RenderResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label, Static, TabbedContent , TabPane, Button, DataTable, Digits
from textual.widget import Widget
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.binding import Binding

class TimerWidget(Widget, can_focus=True):
    # BINDINGS = [
    #         Binding("k", "change_count(1)", "Increment"),  
    #         Binding("j", "change_count(-1)", "Decrement"),
    #     ]

    seconds = minutes = hours = "00"
        
    def compose(self) -> ComposeResult:
        yield Container( 
            Container(
                Label(self.seconds, id="seconds_timer_before"),
                Label(self.minutes, id="minutes_timer_before"),
                Label(self.hours, id="hours_timer_before"),
            id="timer_labels_container_before"),
            Button("Start", id="timer_start"),
        id="make_timer_container_before")

        yield Container(
            Container(
                Label(self.seconds, id="seconds_timer_after"),
                Label(self.minutes, id="minutes_timer_after"),
                Label(self.hours, id="hours_timer_after"),
            id="timer_labels_container_after"),
            Container(
                Button("Delete", id="timer_delete"),
                Button("Pause", id="timer_pause"),
                Button("Start Over", id="timer_start_over"),
                id="timer_buttons_container"),
            id="make_timer_container_after"
            )
        


    # def action_change_count(self, amount: int) -> None:  
    #     self.seconds = "02"

    def on_mount(self) -> None:
        pass