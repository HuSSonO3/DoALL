from textual.app import App, events, ComposeResult
from textual.widgets import Button, Header,  Footer, Label, Tabs, TabbedContent , TabPane, Placeholder, Select
from textual.events import Key
from tabs.central import NoteTakingTab, ClockTab, MusicTab, GamesTab, TodoTab, CheatSheetTab

class DoAllApp(App):
    """Demonstrates the Tabs widget."""

    CSS_PATH = ["text.tcss", "./tabs/noting/noting.tcss", "./tabs/clock/clock.tcss", "./tabs/music/music.tcss", "./tabs/games/games.tcss", "./tabs/todos/todos.tcss", "./tabs/cheats/cheats.tcss"]

    TAB_OPTIONS = [
        ("Note Taker", NoteTakingTab("Note Taker", id="note_taker")),
        ("Clock", ClockTab("Clock", id="clock")),
        ("Music", MusicTab("Music", id="music")),
        ("Games", GamesTab("Games", id="games")),
        ("Todos", TodoTab("Todos", id="todos")),
        ("Cheat Sheets", CheatSheetTab("Cheat Sheets", id="cheat_sheets")),
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

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tab-select":
            return  # only handle the tab-picker Select

        if event.value == Select.BLANK or event.value == Select.NULL:
            return  # nothing selected

        # add new tabs
        content = self.query_one(TabbedContent)
        if not event.value in self.OPEN_TABS:
            await content.add_pane(event.value)
            self.OPEN_TABS.append(event.value)

        self.query_one(TabbedContent).active = event.value.id
        self.query_one("#tab-select", Select).clear()
        
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