from textual.app import App, ComposeResult
from textual.widgets import Footer, Label, Tabs, TabbedContent, TabPane, Select
from textual.containers import Container, Horizontal
from tabs.central import NoteTakingTab, ClockTab, MusicTab, GamesTab, TodoTab, CheatSheetTab, TimeZoneTab, JsonToolTab, ColorPickerTab, BaseConverterTab, LoremTab, MoneyTab, BudgetTab, RandomPickerTab, UnitConverterTab, RegexTesterTab, CsvViewerTab, SubnetCalcTab, JobTrackerTab, CountdownTab, WordCounterTab

class DoAllApp(App):
    """Demonstrates the Tabs widget."""

    CSS_PATH = ["text.tcss", "./tabs/noting/noting.tcss", "./tabs/clock/clock.tcss", "./tabs/music/music.tcss", "./tabs/games/games.tcss", "./tabs/todos/todos.tcss", "./tabs/cheats/cheats.tcss", "./tabs/timezones/timezones.tcss", "./tabs/json_tool/json_tool.tcss", "./tabs/color_picker/color_picker.tcss", "./tabs/base_converter/base_converter.tcss", "./tabs/lorem/lorem.tcss", "./tabs/money/money.tcss", "./tabs/budget/budget.tcss", "./tabs/random_picker/random_picker.tcss", "./tabs/unit_converter/unit_converter.tcss", "./tabs/regex_tester/regex_tester.tcss", "./tabs/csv_viewer/csv_viewer.tcss", "./tabs/subnet_calc/subnet_calc.tcss", "./tabs/job_tracker/job_tracker.tcss", "./tabs/countdown/countdown.tcss", "./tabs/word_counter/word_counter.tcss"]

    TAB_OPTIONS = [
        ("[dim]── Time & Planning ──[/]", None),
        ("Clock", ClockTab("Clock", id="clock")),
        ("Time Zones", TimeZoneTab("Time Zones", id="time_zones")),
        ("Countdown", CountdownTab("Countdown", id="countdown")),
        ("Job Tracker", JobTrackerTab("Job Tracker", id="job_tracker")),

        ("[dim]── Writing & Notes ──[/]", None),
        ("Note Taker", NoteTakingTab("Note Taker", id="note_taker")),
        ("Todos", TodoTab("Todos", id="todos")),
        ("Cheat Sheets", CheatSheetTab("Cheat Sheets", id="cheat_sheets")),
        ("Word Counter", WordCounterTab("Word Counter", id="word_counter")),

        ("[dim]── Finance ──[/]", None),
        ("Money Tracker", MoneyTab("Money Tracker", id="money")),
        ("Budget Tracker", BudgetTab("Budget Tracker", id="budget")),

        ("[dim]── Developer Tools ──[/]", None),
        ("JSON Tool", JsonToolTab("JSON Tool", id="json_tool")),
        ("Base Converter", BaseConverterTab("Base Converter", id="base_converter")),
        ("Regex Tester", RegexTesterTab("Regex Tester", id="regex_tester")),
        ("CSV Viewer", CsvViewerTab("CSV Viewer", id="csv_viewer")),
        ("Subnet Calc", SubnetCalcTab("Subnet Calc", id="subnet_calc")),
        ("Lorem Ipsum", LoremTab("Lorem Ipsum", id="lorem")),

        ("[dim]── Converters & Calculators ──[/]", None),
        ("Unit Converter", UnitConverterTab("Unit Converter", id="unit_converter")),
        ("Color Picker", ColorPickerTab("Color Picker", id="color_picker")),
        ("Random Picker", RandomPickerTab("Random Picker", id="random_picker")),

        ("[dim]── Entertainment ──[/]", None),
        ("Music", MusicTab("Music", id="music")),
        ("Games", GamesTab("Games", id="games")),
    ]

    OPEN_TABS = []

    BINDINGS = [
    ("x", "exit", "Exit Tab (Except '+')"),

    ]

    def compose(self) -> ComposeResult:
        with TabbedContent(id="tabbed"):
            with TabPane("+", id="add"):
                with Container(id="launcher"):
                    yield Label(
                        "[bold $accent]\n"
                        "░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      \n"
                        "░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓████████▓▒░",
                        id="launcher_logo"
                    )
                    yield Label(
                        "[dim]Your all-in-one terminal dashboard[/]",
                        id="launcher_subtitle"
                    )
                    yield Label("Pick a tool:", id="launcher_prompt")
                    yield Select(self.TAB_OPTIONS, prompt="Choose...", id="tab-select")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the tabs when the app starts."""
        self.query_one(Tabs).focus()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tab-select":
            return
        if event.value == Select.BLANK or event.value == Select.NULL or event.value is None:
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
