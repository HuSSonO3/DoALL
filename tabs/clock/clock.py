from textual.app import ComposeResult
from textual.widgets import TabPane, TabbedContent
from .stopwatch import StopwatchWidget
from .timer import TimerWidget
from .alarm import AlarmWidget

class ClockTab(TabPane):
        
    def compose(self) -> ComposeResult:
        with TabbedContent(id="clockTabbed"):
            with TabPane("Alarm", id="alarm"):
                yield AlarmWidget()
            with TabPane("Timer", id="timer"):
                yield TimerWidget()
            with TabPane("Stopwatch", id="stopwatch"):
                yield StopwatchWidget()

        
            

