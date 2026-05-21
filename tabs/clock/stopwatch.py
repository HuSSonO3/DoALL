from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Digits
from textual.containers import Container
from datetime import datetime, timedelta
import time

class StopwatchWidget(Widget):

    def compose(self) -> ComposeResult:
        yield Container(
            Container(Digits("", id="stopwatch_digits"),id="stop_watch_digits_container"),
            Container(
                Button("Start", id="stopwatch_start"),
                Button("Lap", id="stopwatch_lap"),
                id ="stopwatch_button_container"),
            id="stopwatch_container")
        yield DataTable(id="stopwatch_lap_table")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        button_label = event.button.label
        self.log(button_id)
        if(button_id == 'stopwatch_start' and button_label == 'Start'):
            self.start_stopwatch()
        elif(button_id == 'stopwatch_lap' and button_label == 'Lap'):
            self.add_lap()
        elif(button_id == 'stopwatch_start' and button_label == 'Pause'):
            self.pause_stopwatch()
        elif(button_id == 'stopwatch_start' and button_label == 'Resume'):
            self.resume_stopwatch()
        elif (button_id == 'stopwatch_lap' and button_label == 'Clear'):
            self.clear_stopwatch()
        
    def on_mount(self) -> None:
        clock = "00:00:00:00"
        self.query_one("#stopwatch_digits", Digits).update(f"{clock}")
        table = self.query_one("#stopwatch_lap_table", DataTable)
        table.add_columns("Time", "Lap Number")
        self.last_lap_time = 0.0
        self.lap_no = 1
        
    def replace_buttons(self, status) -> None:
        container = self.query_one("#stopwatch_button_container", Container)
        r_start = self.query_one("#stopwatch_start", Button)
        r_lap = self.query_one("#stopwatch_lap", Button)

        if status == "start":
            r_start.label = "Pause"
        
        elif status == "paused":
            r_start.label = "Resume"
            r_lap.label = "Clear"

        elif status == "resumed":
            r_start.label = "Pause"
            r_lap.label = "Lap"

        elif status == "cleared":
            r_start.label = "Start"
            r_lap.label = "Lap"


    def start_stopwatch(self) -> None:
        self.replace_buttons("start")
        self.original_time = time.perf_counter()
        # self.query_one(Digits).update(f"{original_time}")
        self.my_stopwatch = self.set_interval(0.001, self.update_clock)

    
    def update_clock(self) -> None:
        self.current_time = time.perf_counter()
        self.diff = self.current_time - self.original_time
        updated_time = timedelta(seconds=round(self.diff, 2))
        military_time = (datetime.min + updated_time).strftime("%H:%M:%S:%f")[:-4]
        self.query_one("#stopwatch_digits", Digits).update(f"{military_time}")
        

    def add_lap(self) -> None:
        table = self.query_one("#stopwatch_lap_table", DataTable)
        lap_time = self.diff - self.last_lap_time 
        self.last_lap_time = self.diff 
        table.add_row(lap_time, self.lap_no)
        self.lap_no += 1

    def pause_stopwatch(self) -> None:
        self.replace_buttons("paused")
        self.paused_time = self.diff  
        self.my_stopwatch.pause()

    def resume_stopwatch(self) -> None:
        self.replace_buttons("resumed")
        self.original_time = time.perf_counter() - self.paused_time 
        self.my_stopwatch.resume()

    def clear_stopwatch(self) -> None:
        self.replace_buttons("cleared")
        self.my_stopwatch.stop()
        now = "00:00:00"
        clock = datetime.strptime(now, "%H:%M:%S")
        self.query_one("#stopwatch_digits", Digits).update(f"{clock:%T}")
        table = self.query_one("#stopwatch_lap_table", DataTable)
        table.clear()
        self.last_lap_time = 0.0
        self.lap_no = 1
        