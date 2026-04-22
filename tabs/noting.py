from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane

class DashboardTab(TabPane):
    
    def compose(self) -> ComposeResult:
            
        yield Placeholder("Dashboard Screen")
            

