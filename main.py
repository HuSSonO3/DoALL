from textual.app import App, events, ComposeResult
from textual.widgets import Button, Header,  Footer, Label, Tabs, TabbedContent , TabPane, Placeholder, Select
from textual.events import Key
from tabs.central import DashboardTab, TimerTab

class DoAllApp(App):
    """Demonstrates the Tabs widget."""

    
    CSS_PATH = "text.tcss"

    TAB_OPTIONS = [
        ("red", DashboardTab("Dashboard", id="Dashboard")),
        ("blue", TimerTab("IT", id="IT")),
    ]

    OPEN_TABS = []

    BINDINGS = [
    ("x", "exit", "Exit Tab (Except '+')"),

    ]

    # MODES = {
    #     "dashboard": DashboardScreen,  
    # }


        
    def compose(self) -> ComposeResult:
 
        with TabbedContent(id="tabbed"):
            with TabPane("+", id="add"):
                yield Label("Pick a tab:")
                yield Select(self.TAB_OPTIONS, prompt="Choose...", id="tab-select")
                
        yield Footer()

        
    def on_mount(self) -> None:
        """Focus the tabs when the app starts."""
            
        self.query_one(Tabs).focus()
        # tabbed_content = self.query_one(TabbedContent)
        # active_tab = tabbed_content.active  # Returns the id of the active tab
        # self.log("PEKAPOO")

    def on_select_changed(self, event: Select.Changed) -> None:
        
        if event.value == Select.BLANK or  event.value == Select.NULL:
            return  # nothing selected

        # add new tabs
        content = self.query_one(TabbedContent)
        if not event.value in self.OPEN_TABS:
            content.add_pane(event.value)
            self.OPEN_TABS.append(event.value)
        else: 
            self.log("TESTTTT")

        new_tab = event.value.id
        
        select = self.query_one(Select)
        select.clear()

        self.call_after_refresh(lambda: setattr(self.query_one(TabbedContent), 'active', new_tab))
        
    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle TabActivated message sent by Tabs."""
        # active_pane = event.pane  # The TabPane widget
        # active_tab = event.tab    # The Tab widget
        # self.log(active_tab.id)      # The tab's id/name
        # if(active_tab.id == "--content-tab-add"):
        #     yield Label()
        
    async def action_exit(self) -> None:
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.get_pane(tabbed_content.active)
        if(not active_pane.id == "add"):     
            await tabbed_content.remove_pane(active_pane.id)
            self.OPEN_TABS.remove(active_pane)


if __name__ == "__main__":
    app = DoAllApp()
    app.run()