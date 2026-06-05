import csv
import io

from textual.app import ComposeResult
from textual.widgets import TabPane, Select, Label, DataTable, TextArea
from textual.widget import Widget
from textual.containers import Container, Horizontal


class CsvViewerWidget(Widget):

    def compose(self) -> ComposeResult:
        with Container(id="csv_container"):
            yield Label("[bold]CSV Viewer[/]", id="csv_title")

            with Horizontal(id="csv_controls"):
                yield Select(
                    [("Comma (,)", ","), ("Tab", "\t"), ("Pipe (|)", "|"),
                     ("Semicolon (;)", ";"), ("Space", " ")],
                    value=",", allow_blank=False, id="csv_delimiter"
                )
                yield Label("", id="csv_stats")

            yield TextArea.code_editor("", id="csv_input")

            yield Label("", id="csv_status")

            yield DataTable(id="csv_table")

    def on_mount(self):
        self.query_one("#csv_input", TextArea).focus()
        self._parse_timer = None

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "csv_delimiter":
            self._parse()

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id == "csv_input":
            if self._parse_timer:
                self._parse_timer.stop()
            self._parse_timer = self.set_timer(0.3, self._parse)

    def _parse(self):
        text = self.query_one("#csv_input", TextArea).text
        delimiter = self.query_one("#csv_delimiter", Select).value
        status = self.query_one("#csv_status", Label)
        stats = self.query_one("#csv_stats", Label)
        table = self.query_one("#csv_table", DataTable)

        table.clear(columns=True)
        stats.update("")
        status.update("")

        if not text.strip():
            return

        try:
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            rows = list(reader)
        except Exception as e:
            status.update(f"[bold red]Parse error: {e}[/]")
            return

        if not rows:
            status.update("[dim]No data found.[/]")
            return

        # Find the widest row to determine column count
        max_cols = max(len(r) for r in rows)

        # First row as headers, pad with Col N placeholders
        headers = list(rows[0])
        for i in range(len(headers), max_cols):
            headers.append(f"Col {i + 1}")

        table.add_columns(*headers)
        table.cursor_type = "row"

        # Add data rows, padding each to max_cols
        data = rows[1:]
        for r, row in enumerate(data):
            padded = list(row)
            for _ in range(len(padded), max_cols):
                padded.append("")
            table.add_row(*padded, key=str(r))

        stats.update(f"[dim]{len(data)} row(s) × {max_cols} column(s)[/]")


class CsvViewerTab(TabPane):
    def compose(self) -> ComposeResult:
        yield CsvViewerWidget()
