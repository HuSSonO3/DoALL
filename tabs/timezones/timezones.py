from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Input, Label, Select, TabPane
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import os

from .data import COUNTRIES, REFERENCE_ZONES, OFFSETS

class TimeZoneWidget(Widget, can_focus=True):
    """Country time converter + UTC offset reference table."""

    BINDINGS = [
        Binding("ctrl+n", "now", "Now"),
    ]

    def __init__(self):
        super().__init__()
        self._country_rows: list[tuple] = []
        self._offset_rows: list[tuple] = []

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("View:"),
                Select(
                    [("Countries", "countries"), ("UTC Offsets", "offsets")],
                    value="countries",
                    id="tz_mode",
                    allow_blank=False,
                ),
                id="tz_mode_row",
            ),
            Horizontal(
                Button("Now", id="tz_now", variant="primary"),
                Label("Date:"),
                Input(placeholder="YYYY-MM-DD", id="tz_date"),
                Label("Time:"),
                Input(placeholder="HH:MM", id="tz_time"),
                Label("Zone:"),
                Select(
                    [(name, key) for name, key in REFERENCE_ZONES],
                    value="America/New_York",
                    id="tz_reference",
                    allow_blank=False,
                ),
                Button("Convert", id="tz_convert"),
                id="tz_controls",
            ),
            Input(placeholder="Search...", id="tz_search"),
            DataTable(id="tz_table_countries"),
            DataTable(id="tz_table_offsets"),
            id="tz_container",
        )

    def on_mount(self) -> None:
        now = datetime.now(ZoneInfo("America/New_York"))
        self.query_one("#tz_date", Input).value = now.strftime("%Y-%m-%d")
        self.query_one("#tz_time", Input).value = now.strftime("%H:%M")

        countries = self.query_one("#tz_table_countries", DataTable)
        countries.add_columns("Country", "Local Time", "Offset", "Day")
        countries.cursor_type = "row"

        offsets = self.query_one("#tz_table_offsets", DataTable)
        offsets.add_columns("UTC / GMT", "Current Time", "Abbreviations / Locations")
        offsets.cursor_type = "row"

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "tz_mode":
            self._refresh_table()

    def _is_offset_mode(self) -> bool:
        return self.query_one("#tz_mode", Select).value == "offsets"

    # ------------------------------------------------------------------
    # Table visibility
    # ------------------------------------------------------------------

    def _show_table(self, visible_id: str) -> None:
        countries = self.query_one("#tz_table_countries", DataTable)
        offsets = self.query_one("#tz_table_offsets", DataTable)
        search = self.query_one("#tz_search", Input)
        countries.display = "block" if visible_id == "tz_table_countries" else "none"
        offsets.display = "block" if visible_id == "tz_table_offsets" else "none"
        # Reset search on mode switch
        if search.value:
            search.value = ""

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "tz_search":
            if self._is_offset_mode():
                self._render_offsets(event.value)
            else:
                self._render_countries(event.value)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tz_now":
            self.action_now()
        elif event.button.id == "tz_convert":
            self._refresh_table()

    # ------------------------------------------------------------------
    # Controls visibility
    # ------------------------------------------------------------------

    def _set_controls_visible(self, visible: bool) -> None:
        controls = self.query_one("#tz_controls", Horizontal)
        controls.display = "block" if visible else "none"

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_now(self) -> None:
        if self._is_offset_mode():
            self._refresh_table()
            return

        tz_key = self.query_one("#tz_reference", Select).value
        now = datetime.now(ZoneInfo(tz_key))
        self.query_one("#tz_date", Input).value = now.strftime("%Y-%m-%d")
        self.query_one("#tz_time", Input).value = now.strftime("%H:%M")
        self._refresh_table()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_inputs(self) -> datetime | None:
        date_str = self.query_one("#tz_date", Input).value.strip()
        time_str = self.query_one("#tz_time", Input).value.strip()

        if not date_str:
            self.notify("Date is required (format: YYYY-MM-DD).", severity="error")
            self.query_one("#tz_date", Input).focus()
            return None

        if not time_str:
            self.notify("Time is required (format: HH:MM).", severity="error")
            self.query_one("#tz_time", Input).focus()
            return None

        parts = date_str.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            self.notify(
                f"Invalid date '[bold]{date_str}[/]'. Use YYYY-MM-DD (e.g. 2026-06-01).",
                severity="error",
            )
            self.query_one("#tz_date", Input).focus()
            return None

        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        if not (1 <= m <= 12):
            self.notify(
                f"Invalid month '[bold]{m}[/]'. Month must be 01–12.",
                severity="error",
            )
            self.query_one("#tz_date", Input).focus()
            return None

        try:
            base = datetime(y, m, d)
        except ValueError:
            self.notify(
                f"Invalid date '[bold]{date_str}[/]'. Day is out of range for that month.",
                severity="error",
            )
            self.query_one("#tz_date", Input).focus()
            return None

        parts = time_str.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            self.notify(
                f"Invalid time '[bold]{time_str}[/]'. Use HH:MM (e.g. 14:30).",
                severity="error",
            )
            self.query_one("#tz_time", Input).focus()
            return None

        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23):
            self.notify(
                f"Invalid hour '[bold]{hour}[/]'. Hour must be 00–23.",
                severity="error",
            )
            self.query_one("#tz_time", Input).focus()
            return None
        if not (0 <= minute <= 59):
            self.notify(
                f"Invalid minute '[bold]{minute}[/]'. Minute must be 00–59.",
                severity="error",
            )
            self.query_one("#tz_time", Input).focus()
            return None

        try:
            return datetime(y, m, d, hour, minute)
        except ValueError:
            self.notify("Invalid date/time combination.", severity="error")
            return None

    # ------------------------------------------------------------------
    # Table refresh
    # ------------------------------------------------------------------

    def _refresh_table(self) -> None:
        if self._is_offset_mode():
            self._set_controls_visible(False)
            self._show_table("tz_table_offsets")
            self._build_offset_data()
            self._render_offsets()
        else:
            self._set_controls_visible(True)
            self._show_table("tz_table_countries")
            self._build_country_data()
            self._render_countries()

    def _build_country_data(self) -> None:
        ref_dt = self._validate_inputs()
        if ref_dt is None:
            self._country_rows = []
            return

        ref_tz_key = self.query_one("#tz_reference", Select).value
        ref_zone = ZoneInfo(ref_tz_key)
        ref_local = ref_dt.replace(tzinfo=ref_zone)
        utc_instant = ref_local.astimezone(ZoneInfo("UTC"))

        rows = []
        for country_name, tz_key in COUNTRIES:
            try:
                local = utc_instant.astimezone(ZoneInfo(tz_key))
            except Exception:
                continue

            time_label = local.strftime("%H:%M")
            offset = local.strftime("UTC%z")
            offset_str = self._format_offset(offset)

            day_diff = local.date() - utc_instant.date()
            day = self._day_label(day_diff)

            rows.append((country_name, time_label, offset_str, day, f"{tz_key}|{country_name}"))
        self._country_rows = rows

    def _render_countries(self, filter_text: str = "") -> None:
        table = self.query_one("#tz_table_countries", DataTable)
        table.clear()
        q = filter_text.lower()
        for name, time_label, offset_str, day, key in self._country_rows:
            if q and q not in name.lower():
                continue
            table.add_row(name, time_label, offset_str, day, key=key)

    def _build_offset_data(self) -> None:
        now_utc = datetime.now(ZoneInfo("UTC"))
        rows = []
        for label, hours, desc in OFFSETS:
            local = now_utc + timedelta(hours=hours)
            time_label = local.strftime("%H:%M")
            day_diff = local.date() - now_utc.date()
            day = self._day_label(day_diff)
            if day:
                time_label = f"{time_label}  {day}"

            # Build GMT-aware label: UTC-5 / GMT-5, UTC+5:30 / GMT+5:30, UTC±0 / GMT
            if label == "UTC±0":
                gmt_label = "UTC±0 / GMT"
            else:
                gmt_part = label.replace("UTC", "GMT")
                gmt_label = f"{label} / {gmt_part}"

            rows.append((gmt_label, time_label, desc, label))
        self._offset_rows = rows

    def _render_offsets(self, filter_text: str = "") -> None:
        table = self.query_one("#tz_table_offsets", DataTable)
        table.clear()
        q = filter_text.lower()
        for gmt_label, time_label, desc, key in self._offset_rows:
            if q and q not in gmt_label.lower() and q not in desc.lower():
                continue
            table.add_row(gmt_label, time_label, desc, key=key)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_offset(raw: str) -> str:
        if len(raw) >= 8:
            sign, h, m = raw[3], raw[4:6], raw[6:8]
            h = h.lstrip("0") or "0"
            if m == "00":
                return f"UTC{sign}{h}"
            return f"UTC{sign}{h}:{m}"
        return raw

    @staticmethod
    def _day_label(diff: timedelta) -> str:
        if diff.days == 1:
            return "→ tomorrow"
        elif diff.days == -1:
            return "→ yesterday"
        elif diff.days > 1:
            return f"→ +{diff.days}d"
        elif diff.days < -1:
            return f"→ {diff.days}d"
        return ""


# ---------------------------------------------------------------------------
# TabPane wrapper
# ---------------------------------------------------------------------------

class TimeZoneTab(TabPane):
    """TabPane wrapper for the Time Zone Converter module."""

    DEFAULT_CSS = open(os.path.join(os.path.dirname(__file__), "timezones.tcss")).read()

    def compose(self) -> ComposeResult:
        yield TimeZoneWidget()
