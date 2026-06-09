"""Unit Converter — widget and tab wrapper."""

from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Select, Label, Button
from textual.widget import Widget
from textual.containers import Container, Horizontal
from textual.binding import Binding

from .conversions import UNIT_CATEGORIES, convert_standard, convert_temperature
from .db import init_db, get_rates


class UnitConverterWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("s", "swap", "Swap Units"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._currency_rates = {}
        self._currency_ts = None
        self._suppress_change = False

    def compose(self) -> ComposeResult:
        with Container(id="uc_container"):
            yield Label("[bold]Unit Converter[/]", id="uc_title")

            yield Select(
                [(cat, cat) for cat in UNIT_CATEGORIES] + [("Currency", "Currency")],
                value="Length", allow_blank=False, id="uc_category"
            )

            with Horizontal(id="uc_input_row"):
                yield Input(placeholder="Value", value="1", id="uc_input")
                yield Select([], id="uc_from")

            with Horizontal(id="uc_swap_row"):
                yield Button("⇅ Swap", id="uc_swap_btn")

            with Horizontal(id="uc_output_row"):
                yield Input(placeholder="Result", id="uc_output", disabled=True)
                yield Select([], id="uc_to")

            yield Label("", id="uc_rate_info")

    def on_mount(self):
        init_db()
        self._populate_category("Length")
        self.query_one("#uc_input", Input).focus()
        self._try_convert()

    def on_select_changed(self, event: Select.Changed):
        if self._suppress_change:
            return
        sid = event.select.id
        if sid == "uc_category":
            self._populate_category(event.value)
            self._try_convert()
        elif sid in ("uc_from", "uc_to"):
            self._try_convert()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "uc_input":
            self._try_convert()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "uc_input":
            self._try_convert()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "uc_swap_btn":
            self.action_swap()

    def action_swap(self):
        from_sel = self.query_one("#uc_from", Select)
        to_sel = self.query_one("#uc_to", Select)
        from_val = from_sel.value
        to_val = to_sel.value
        if from_val == Select.BLANK or to_val == Select.BLANK:
            return
        self._suppress_change = True
        from_sel.value = to_val
        to_sel.value = from_val
        self._suppress_change = False
        result = self.query_one("#uc_output", Input).value
        if result:
            self.query_one("#uc_input", Input).value = result
        self._try_convert()

    def _populate_category(self, category):
        self._suppress_change = True

        if category == "Currency":
            rates, ts = get_rates()
            self._currency_rates = rates
            self._currency_ts = ts
            units = list(rates.keys())
            units.sort()
            info = self.query_one("#uc_rate_info", Label)
            if ts:
                dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                info.update(f"[dim]Rates as of {dt} (refreshes daily)[/]")
            else:
                info.update("[dim]Could not fetch rates. Using cached data if available.[/]")
        else:
            units = list(UNIT_CATEGORIES[category].keys())
            self.query_one("#uc_rate_info", Label).update("")

        options = [(u, u) for u in units]
        self.query_one("#uc_from", Select).set_options(options)
        self.query_one("#uc_to", Select).set_options(options)
        if len(units) >= 2:
            self.query_one("#uc_from", Select).value = units[0]
            self.query_one("#uc_to", Select).value = units[1]

        self._suppress_change = False

    def _try_convert(self):
        category = self.query_one("#uc_category", Select).value
        from_unit = self.query_one("#uc_from", Select).value
        to_unit = self.query_one("#uc_to", Select).value
        amount_str = self.query_one("#uc_input", Input).value.strip()
        output = self.query_one("#uc_output", Input)

        if not amount_str:
            output.value = ""
            return
        try:
            amount = float(amount_str)
        except ValueError:
            output.value = "Invalid"
            return

        if from_unit == Select.BLANK or to_unit == Select.BLANK:
            return

        try:
            if category == "Temperature":
                result = convert_temperature(amount, from_unit, to_unit)
            elif category == "Currency":
                result = self._convert_currency(amount, from_unit, to_unit)
            else:
                result = convert_standard(category, amount, from_unit, to_unit)
        except Exception:
            output.value = "Error"
            return

        if abs(result) < 0.000001 and result != 0:
            output.value = f"{result:.10g}"
        elif abs(result) >= 1_000_000 or (abs(result) < 0.01 and result != 0):
            output.value = f"{result:,.6f}".rstrip("0").rstrip(".")
        else:
            output.value = f"{result:,.4f}".rstrip("0").rstrip(".")

    def _convert_currency(self, amount, from_cur, to_cur):
        """Convert using USD-based rates. rates[X] = how many X per 1 USD."""
        rates = self._currency_rates
        if not rates or from_cur not in rates or to_cur not in rates:
            raise ValueError("Rate not available")
        usd = amount / rates[from_cur]
        return usd * rates[to_cur]


class UnitConverterTab(TabPane):
    def compose(self) -> ComposeResult:
        yield UnitConverterWidget()
