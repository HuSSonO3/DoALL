import re

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, DataTable, TextArea
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding


class RegexTesterWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("enter", "test", "Test Regex"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="re_container"):
            yield Label("[bold]Regex Tester[/]", id="re_title")

            with Horizontal(id="re_pattern_row"):
                yield Label("/", id="re_slash_open")
                yield Input(placeholder="Enter regex pattern...", id="re_pattern")
                yield Label("/", id="re_slash_close")
                yield Input(placeholder="Flags (e.g. i, m, s, im)", id="re_flags")

            yield Label("Test String", id="re_test_label")
            yield TextArea.code_editor("", language="regex", id="re_test_input")

            yield Label("", id="re_status")

            yield DataTable(id="re_results")

    def on_mount(self):
        self.query_one("#re_pattern", Input).focus()

        table = self.query_one("#re_results", DataTable)
        table.add_columns("Match #", "Start", "End", "Match", "Groups")
        table.cursor_type = "row"

    def on_input_changed(self, event: Input.Changed):
        if event.input.id in ("re_pattern", "re_flags"):
            self._run_test()

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id == "re_test_input":
            self._run_test()

    def _run_test(self):
        pattern_str = self.query_one("#re_pattern", Input).value
        flags_str = self.query_one("#re_flags", Input).value.strip()
        test_text = self.query_one("#re_test_input", TextArea).text
        status = self.query_one("#re_status", Label)
        table = self.query_one("#re_results", DataTable)
        table.clear()

        if not pattern_str:
            status.update("")
            return

        # Parse flags
        flags = 0
        flag_map = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}
        for ch in flags_str:
            if ch in flag_map:
                flags |= flag_map[ch]
            elif ch.strip():
                status.update(f"[bold red]Unknown flag: '{ch}'[/]")
                return

        try:
            compiled = re.compile(pattern_str, flags)
        except re.error as e:
            status.update(f"[bold red]Invalid pattern: {e}[/]")
            return

        matches = list(compiled.finditer(test_text))
        if not matches:
            status.update("[dim]No matches found.[/]")
            return

        status.update(f"[dim]{len(matches)} match(es) found[/]")

        for i, m in enumerate(matches, 1):
            groups = ", ".join(
                f"{j}: {g!r}"
                for j, g in enumerate(m.groups(), 1)
            ) if m.groups() else "—"
            table.add_row(
                str(i),
                str(m.start()),
                str(m.end()),
                m.group()[:60],
                groups[:60],
            )


class RegexTesterTab(TabPane):
    def compose(self) -> ComposeResult:
        yield RegexTesterWidget()
