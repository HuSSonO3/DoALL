from textual.app import App, ComposeResult
from textual.widgets import Footer, Label, Tabs, TabbedContent, TabPane, Select
from textual.containers import Container, Horizontal
from tabs.central import NoteTakingTab, ClockTab, MusicTab, GamesTab, TodoTab, CheatSheetTab, TimeZoneTab, JsonToolTab, ColorPickerTab, BaseConverterTab, LoremTab, MoneyTab, BudgetTab, RandomPickerTab, UnitConverterTab, RegexTesterTab, CsvViewerTab, SubnetCalcTab, JobTrackerTab, CountdownTab, WordCounterTab, PortCheckerTab, ChangelogTab, QRToolTab, GitignoreBuilderTab, TypingTestTab, RecipesTab, HabitTab

class DoAllApp(App):
    """Demonstrates the Tabs widget."""

    CSS_PATH = ["text.tcss", "./tabs/noting/noting.tcss", "./tabs/clock/clock.tcss", "./tabs/music/music.tcss", "./tabs/games/games.tcss", "./tabs/todos/todos.tcss", "./tabs/cheats/cheats.tcss", "./tabs/timezones/timezones.tcss", "./tabs/json_tool/json_tool.tcss", "./tabs/color_picker/color_picker.tcss", "./tabs/base_converter/base_converter.tcss", "./tabs/lorem/lorem.tcss", "./tabs/money/money.tcss", "./tabs/budget/budget.tcss", "./tabs/random_picker/random_picker.tcss", "./tabs/unit_converter/unit_converter.tcss", "./tabs/regex_tester/regex_tester.tcss", "./tabs/csv_viewer/csv_viewer.tcss", "./tabs/subnet_calc/subnet_calc.tcss", "./tabs/job_tracker/job_tracker.tcss", "./tabs/countdown/countdown.tcss", "./tabs/word_counter/word_counter.tcss", "./tabs/port_checker/port_checker.tcss", "./tabs/changelog/changelog.tcss", "./tabs/qr_extractor/qr_extractor.tcss", "./tabs/gitignore_builder/gitignore_builder.tcss", "./tabs/typing_test/typing_test.tcss", "./tabs/recipes/recipes.tcss", "./tabs/habits/habits.tcss"]

    TAB_CATEGORIES = {
        "Time & Planning": [
            ("Clock", ClockTab("Clock", id="clock")),
            ("Time Zones", TimeZoneTab("Time Zones", id="time_zones")),
            ("Countdown", CountdownTab("Countdown", id="countdown")),
            ("Job Tracker", JobTrackerTab("Job Tracker", id="job_tracker")),
        ],
        "Writing & Notes": [
            ("Note Taker", NoteTakingTab("Note Taker", id="note_taker")),
            ("Todos", TodoTab("Todos", id="todos")),
            ("Cheat Sheets", CheatSheetTab("Cheat Sheets", id="cheat_sheets")),
            ("Word Counter", WordCounterTab("Word Counter", id="word_counter")),
        ],
        "Finance": [
            ("Money Tracker", MoneyTab("Money Tracker", id="money")),
            ("Budget Tracker", BudgetTab("Budget Tracker", id="budget")),
        ],
        "Developer Tools": [
            ("JSON Tool", JsonToolTab("JSON Tool", id="json_tool")),
            ("Base Converter", BaseConverterTab("Base Converter", id="base_converter")),
            ("Regex Tester", RegexTesterTab("Regex Tester", id="regex_tester")),
            ("CSV Viewer", CsvViewerTab("CSV Viewer", id="csv_viewer")),
            ("Subnet Calc", SubnetCalcTab("Subnet Calc", id="subnet_calc")),
            ("Port Checker", PortCheckerTab("Port Checker", id="port_checker")),
            ("Changelog Gen", ChangelogTab("Changelog Gen", id="changelog")),
            ("QR Gen & Extract", QRToolTab("QR Gen & Extract", id="qr_tool")),
            ("Gitignore Builder", GitignoreBuilderTab("Gitignore Builder", id="gitignore_builder")),
            ("Lorem Ipsum", LoremTab("Lorem Ipsum", id="lorem")),
        ],
        "Converters & Calc": [
            ("Unit Converter", UnitConverterTab("Unit Converter", id="unit_converter")),
            ("Color Picker", ColorPickerTab("Color Picker", id="color_picker")),
            ("Random Picker", RandomPickerTab("Random Picker", id="random_picker")),
        ],
        "Entertainment": [
            ("Music", MusicTab("Music", id="music")),
            ("Games", GamesTab("Games", id="games")),
            ("Typing Test", TypingTestTab("Typing Test", id="typing_test")),
        ],
        "Life & Home": [
            ("Recipe Manager", RecipesTab("Recipe Manager", id="recipes")),
            ("Habit Tracker", HabitTab("Habit Tracker", id="habits")),
        ],
    }

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
                    with Horizontal(id="launcher_picker"):
                        yield Select(
                            [(cat, cat) for cat in self.TAB_CATEGORIES],
                            prompt="Category...",
                            id="cat-select",
                        )
                        yield Select([], prompt="Tool...", id="tool-select")
                    yield Label(
                        "[dim italic]Known issue: some tools may not auto-switch — "
                        "click the tab or use ← → to navigate[/]",
                        id="launcher_known_issue",
                    )
        yield Footer()

    def on_mount(self) -> None:
        """Focus the tabs when the app starts."""
        self.query_one(Tabs).focus()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "cat-select":
            self._populate_tools(event.value)
        elif event.select.id == "tool-select":
            if event.value not in (Select.BLANK, Select.NULL):
                await self._open_tool(event.value)

    def _populate_tools(self, category: str) -> None:
        tool_select = self.query_one("#tool-select", Select)
        if category == Select.BLANK:
            tool_select.set_options([])
            return
        tools = self.TAB_CATEGORIES.get(category, [])
        tool_select.set_options([(label, pane) for label, pane in tools])

    async def _open_tool(self, tab_pane) -> None:
        if tab_pane is None or tab_pane in (Select.BLANK, Select.NULL):
            return

        content = self.query_one(TabbedContent)

        if tab_pane not in self.OPEN_TABS:
            await content.add_pane(tab_pane)
            self.OPEN_TABS.append(tab_pane)

        content.show_tab(tab_pane.id)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Reset the + tab Selects whenever it becomes active."""
        if event.pane.id == "add":
            self.query_one("#cat-select", Select).clear()
            self.query_one("#tool-select", Select).clear()

    async def action_exit(self) -> None:
        tabbed_content = self.query_one(TabbedContent)
        active_pane = tabbed_content.get_pane(tabbed_content.active)
        if(not active_pane.id == "add"):
            await tabbed_content.remove_pane(active_pane.id)
            self.OPEN_TABS.remove(active_pane)


if __name__ == "__main__":
    app = DoAllApp()
    app.run()
