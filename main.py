from textual.app import App, ComposeResult
from textual.widgets import Footer, Label, Tabs, TabbedContent, TabPane, Select
from tabs.central import NoteTakingTab, ClockTab, MusicTab, GamesTab, TodoTab, CheatSheetTab, TimeZoneTab, JsonToolTab, ColorPickerTab, BaseConverterTab, LoremTab, MoneyTab, BudgetTab, RandomPickerTab, UnitConverterTab, RegexTesterTab, CsvViewerTab, SubnetCalcTab

class DoAllApp(App):
    """Demonstrates the Tabs widget."""

    CSS_PATH = ["text.tcss", "./tabs/noting/noting.tcss", "./tabs/clock/clock.tcss", "./tabs/music/music.tcss", "./tabs/games/games.tcss", "./tabs/todos/todos.tcss", "./tabs/cheats/cheats.tcss", "./tabs/timezones/timezones.tcss", "./tabs/json_tool/json_tool.tcss", "./tabs/color_picker/color_picker.tcss", "./tabs/base_converter/base_converter.tcss", "./tabs/lorem/lorem.tcss", "./tabs/money/money.tcss", "./tabs/budget/budget.tcss", "./tabs/random_picker/random_picker.tcss", "./tabs/unit_converter/unit_converter.tcss", "./tabs/regex_tester/regex_tester.tcss", "./tabs/csv_viewer/csv_viewer.tcss", "./tabs/subnet_calc/subnet_calc.tcss"]

    TAB_OPTIONS = [
        ("Note Taker", NoteTakingTab("Note Taker", id="note_taker")),
        ("Clock", ClockTab("Clock", id="clock")),
        ("Music", MusicTab("Music", id="music")),
        ("Games", GamesTab("Games", id="games")),
        ("Todos", TodoTab("Todos", id="todos")),
        ("Cheat Sheets", CheatSheetTab("Cheat Sheets", id="cheat_sheets")),
        ("Time Zones", TimeZoneTab("Time Zones", id="time_zones")),
        ("JSON Tool", JsonToolTab("JSON Tool", id="json_tool")),
        ("Color Picker", ColorPickerTab("Color Picker", id="color_picker")),
        ("Base Converter", BaseConverterTab("Base Converter", id="base_converter")),
        ("Lorem Ipsum", LoremTab("Lorem Ipsum", id="lorem")),
        ("Money Tracker", MoneyTab("Money Tracker", id="money")),
        ("Budget Tracker", BudgetTab("Budget Tracker", id="budget")),
        ("Random Picker", RandomPickerTab("Random Picker", id="random_picker")),
        ("Unit Converter", UnitConverterTab("Unit Converter", id="unit_converter")),
        ("Regex Tester", RegexTesterTab("Regex Tester", id="regex_tester")),
        ("CSV Viewer", CsvViewerTab("CSV Viewer", id="csv_viewer")),
        ("Subnet Calc", SubnetCalcTab("Subnet Calc", id="subnet_calc")),
    ]

    OPEN_TABS = []

    BINDINGS = [
    ("x", "exit", "Exit Tab (Except '+')"),

    ]

    def compose(self) -> ComposeResult:
        with TabbedContent(id="tabbed"):
            with TabPane("+", id="add"):
                yield Label("Pick a tab:")
                yield Select(self.TAB_OPTIONS, prompt="Choose...", id="tab-select")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the tabs when the app starts."""
        self.query_one(Tabs).focus()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tab-select":
            return
        if event.value == Select.BLANK or event.value == Select.NULL:
            return

        content = self.query_one(TabbedContent)
        tab_pane = event.value

        if tab_pane not in self.OPEN_TABS:
            await content.add_pane(tab_pane)
            self.OPEN_TABS.append(tab_pane)

        # Defer the switch so the Select dropdown has fully closed
        self.call_after_refresh(lambda: setattr(content, "active", tab_pane.id))

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Reset the + tab Select whenever it becomes active."""
        if event.pane.id == "add":
            self.query_one("#tab-select", Select).clear()

    async def action_exit(self) -> None:
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.get_pane(tabbed_content.active)
        if(not active_pane.id == "add"):
            await tabbed_content.remove_pane(active_pane.id)
            self.OPEN_TABS.remove(active_pane)


if __name__ == "__main__":
    app = DoAllApp()
    app.run()
