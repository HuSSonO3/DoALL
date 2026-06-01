from textual.app import ComposeResult
from textual.widgets import Input, Label, Select, Static, TabPane
from textual.widget import Widget
from textual.containers import Horizontal, Vertical


BASES = {
    "bin": {"name": "Binary",      "radix": 2,  "prefix": "0b"},
    "oct": {"name": "Octal",       "radix": 8,  "prefix": "0o"},
    "dec": {"name": "Decimal",     "radix": 10, "prefix": ""},
    "hex": {"name": "Hexadecimal", "radix": 16, "prefix": "0x"},
}

BASE_ORDER = ["bin", "oct", "dec", "hex"]


class BaseConverterWidget(Widget, can_focus=True):

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Source:"),
                Select(
                    [(v["name"], k) for k, v in BASES.items()],
                    value="dec",
                    id="bc_source",
                    allow_blank=False,
                ),
                id="bc_toolbar",
            ),
            Input(placeholder="Enter a number...", id="bc_input"),
            Label("", id="bc_error"),
            Vertical(
                Static("", id="bc_line_bin"),
                Static("", id="bc_line_oct"),
                Static("", id="bc_line_dec"),
                Static("", id="bc_line_hex"),
                Static("", id="bc_line_ascii"),
                id="bc_results",
            ),
            id="bc_container",
        )

    def on_mount(self) -> None:
        self.query_one("#bc_input", Input).focus()

    # ── Live conversion ─────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "bc_input":
            self._convert(event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "bc_source":
            self._convert(self.query_one("#bc_input", Input).value)

    def _convert(self, raw: str) -> None:
        raw = raw.strip()
        error = self.query_one("#bc_error", Label)
        error.update("")

        if not raw:
            for key in BASE_ORDER:
                self.query_one(f"#bc_line_{key}", Static).update("")
            self.query_one("#bc_line_ascii", Static).update("")
            return

        source_key = self.query_one("#bc_source", Select).value
        radix = BASES[source_key]["radix"]
        prefix = BASES[source_key]["prefix"]

        # Strip known prefixes (0b, 0o, 0x) so user can paste hex like 0xFF
        cleaned = raw
        for _, cfg in BASES.items():
            p = cfg["prefix"]
            if p and cleaned.lower().startswith(p):
                cleaned = cleaned[len(p):]
                break

        # Parse from source base
        try:
            value = int(cleaned, radix)
        except ValueError:
            error.update(f"[red]Invalid {BASES[source_key]['name']} number.[/]")
            for key in BASE_ORDER:
                self.query_one(f"#bc_line_{key}", Static).update("")
            self.query_one("#bc_line_ascii", Static).update("")
            return

        # Format in each base
        self.query_one("#bc_line_bin", Static).update(
            f"[bold]Bin[/]  {self._spaced(value, 2, 4)}"
        )
        self.query_one("#bc_line_oct", Static).update(
            f"[bold]Oct[/]  {oct(value)[2:]}"
        )
        self.query_one("#bc_line_dec", Static).update(
            f"[bold]Dec[/]  {value:,}"
        )
        self.query_one("#bc_line_hex", Static).update(
            f"[bold]Hex[/]  {hex(value)[2:].upper()}"
        )

        # ASCII
        if 32 <= value <= 126:
            ascii_repr = f"[bold]ASCII[/] '{chr(value)}'"
        elif 0 <= value <= 255:
            ascii_repr = f"[bold]ASCII[/] [dim](control char: {value})[/]"
        else:
            ascii_repr = f"[bold]ASCII[/] [dim](out of range)[/]"
        self.query_one("#bc_line_ascii", Static).update(ascii_repr)

    @staticmethod
    def _spaced(n: int, base: int, group: int) -> str:
        """Format a number with spaces every `group` digits."""
        if n == 0:
            return "0"
        fmt = bin(n)[2:] if base == 2 else ""
        # Pad to multiple of group
        if len(fmt) % group:
            fmt = fmt.zfill(((len(fmt) // group) + 1) * group)
        return " ".join(fmt[i:i+group] for i in range(0, len(fmt), group))


# ── TabPane ─────────────────────────────────────────────

class BaseConverterTab(TabPane):

    def compose(self) -> ComposeResult:
        yield BaseConverterWidget()
