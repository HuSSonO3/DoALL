from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, Static
from textual.widget import Widget
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.color import Color
from textual import events

SLIDER_CELLS = 24

# Modes define slider count, names, max values, and how to compute cell colors
MODES = {
    "hsl": {
        "sliders": [
            {"name": "Hue",        "max": 360, "unit": "°"},
            {"name": "Saturation",  "max": 100, "unit": "%"},
            {"name": "Lightness",   "max": 100, "unit": "%"},
        ],
        "cell_color": "hsl_cell",
        "from_values": "from_hsl",
        "to_values": "to_hsl",
    },
    "rgb": {
        "sliders": [
            {"name": "Red",   "max": 255, "unit": ""},
            {"name": "Green", "max": 255, "unit": ""},
            {"name": "Blue",  "max": 255, "unit": ""},
        ],
        "cell_color": "rgb_cell",
        "from_values": "from_rgb",
        "to_values": "to_rgb",
    },
}


class SliderPicker(Widget, can_focus=True):

    BINDINGS = [
        Binding("left,h", "decrement", "-"),
        Binding("right,l", "increment", "+"),
        Binding("up,k", "prev_slider", "Prev"),
        Binding("down,j,tab", "next_slider", "Next"),

    ]

    def __init__(self, mode="hsl"):
        super().__init__()
        cfg = MODES[mode]
        self._mode = mode
        self._slider_defs = cfg["sliders"]
        self._num_sliders = len(self._slider_defs)
        self._values = [0] * self._num_sliders
        self._active = 0
        self._cells: list[list[Static]] = []
        self._pointers: list[list[Label]] = []

        # Build slider IDs
        self._slider_ids = [f"cp_slider_{i}" for i in range(self._num_sliders)]
        self._pointer_ids = [f"cp_pointer_{i}" for i in range(self._num_sliders)]
        self._label_ids = [f"cp_label_{i}" for i in range(self._num_sliders)]

    def compose(self) -> ComposeResult:
        children = []
        for i in range(self._num_sliders):
            children.append(Label("", id=self._label_ids[i]))
            children.append(Horizontal(id=self._pointer_ids[i], classes="cp_pointer_row"))
            children.append(Horizontal(id=self._slider_ids[i], classes="cp_slider_row"))

        children.append(
            Horizontal(
                Static("", id="cp_preview_block"),
                Vertical(
                    Label("", id="cp_label_hex"),
                    Label("", id="cp_label_values"),
                    id="cp_preview_info",
                ),
                id="cp_preview_row",
            )
        )
        children.append(
            Horizontal(
                Label("Hex:"),
                Input(placeholder="", id="cp_hex_input"),
                Button("Set", id="cp_hex_set"),
                id="cp_bottom_bar",
            )
        )

        yield Vertical(*children, id="cp_container")

    def on_mount(self) -> None:
        for i in range(self._num_sliders):
            pointer_row = self.query_one(f"#{self._pointer_ids[i]}", Horizontal)
            slider_row = self.query_one(f"#{self._slider_ids[i]}", Horizontal)
            cell_row = []
            ptr_row = []

            for _ in range(SLIDER_CELLS):
                lbl = Label(" ", classes="cp_pointer_label")
                lbl._cp_which = i
                pointer_row.mount(lbl)
                ptr_row.append(lbl)

                cell = Static("", classes="cp_slider_cell")
                cell._cp_which = i
                slider_row.mount(cell)
                cell_row.append(cell)

            self._cells.append(cell_row)
            self._pointers.append(ptr_row)

            self.query_one(f"#{self._label_ids[i]}", Label)._cp_which = i

        self._refresh_cells()
        self._update_preview()

    # ── Refresh ──────────────────────────────────────────────

    def _refresh_cells(self) -> None:
        for i in range(self._num_sliders):
            for j, cell in enumerate(self._cells[i]):
                color = self._cell_color(i, j)
                cell.styles.background = color
        self._update_pointers()
        self._update_labels()

    def _update_pointers(self) -> None:
        for i in range(self._num_sliders):
            mx = self._slider_defs[i]["max"]
            idx = round(self._values[i] / mx * (SLIDER_CELLS - 1)) if mx else 0
            for j, lbl in enumerate(self._pointers[i]):
                lbl.update("[bold]▼[/]" if (j == idx and i == self._active) else " ")

    def _cell_color(self, which: int, pos: int) -> Color:
        if self._mode == "hsl":
            return self._hsl_cell(which, pos)
        else:
            return self._rgb_cell(which, pos)

    def _hsl_cell(self, which: int, pos: int) -> Color:
        h, s, l = self._values
        if which == 0:
            h = round(pos / (SLIDER_CELLS - 1) * 360)
        elif which == 1:
            s = round(pos / (SLIDER_CELLS - 1) * 100)
        else:
            l = round(pos / (SLIDER_CELLS - 1) * 100)
        return Color.from_hsl(h / 360, s / 100, l / 100)

    def _rgb_cell(self, which: int, pos: int) -> Color:
        r, g, b = self._values
        val = round(pos / (SLIDER_CELLS - 1) * 255)
        if which == 0:
            r = val
        elif which == 1:
            g = val
        else:
            b = val
        return Color(r, g, b)

    # ── Actions ──────────────────────────────────────────────

    def action_increment(self) -> None:
        mx = self._slider_defs[self._active]["max"]
        self._values[self._active] = min(self._values[self._active] + 1, mx)
        self._refresh_cells()
        self._update_preview()

    def action_decrement(self) -> None:
        self._values[self._active] = max(self._values[self._active] - 1, 0)
        self._refresh_cells()
        self._update_preview()

    def action_next_slider(self) -> None:
        self._active = (self._active + 1) % self._num_sliders
        self._refresh_cells()

    def action_prev_slider(self) -> None:
        self._active = (self._active - 1) % self._num_sliders
        self._refresh_cells()

    def on_click(self, event: events.Click) -> None:
        w = event.widget
        if w is None:
            return
        which = getattr(w, "_cp_which", None)
        if which is not None and which != self._active:
            self._active = which
            self._refresh_cells()

    # ── Labels ───────────────────────────────────────────────

    def _update_labels(self) -> None:
        for i in range(self._num_sliders):
            name = self._slider_defs[i]["name"]
            val = self._values[i]
            unit = self._slider_defs[i]["unit"]
            marker = " [dim](active)[/]" if i == self._active else ""
            self.query_one(f"#{self._label_ids[i]}", Label).update(
                f"[bold]{name}[/]         {val}{unit}{marker}"
            )

    # ── Preview ──────────────────────────────────────────────

    def _current_color(self) -> Color:
        if self._mode == "hsl":
            h, s, l = self._values
            return Color.from_hsl(h / 360, s / 100, l / 100)
        else:
            r, g, b = self._values
            return Color(r, g, b)

    def _update_preview(self) -> None:
        color = self._current_color()
        hex_str = color.hex
        r, g, b = color.rgb
        h, s, l = color.hsl

        self.query_one("#cp_preview_block", Static).styles.background = color
        self.query_one("#cp_label_hex", Label).update(f"[bold]Hex:[/] {hex_str}")

        if self._mode == "hsl":
            self.query_one("#cp_label_values", Label).update(
                f"[bold]HSL:[/] {int(round(h))}°  {int(round(s * 100))}%  {int(round(l * 100))}%"
            )
        else:
            self.query_one("#cp_label_values", Label).update(
                f"[bold]RGB:[/] {r}  {g}  {b}"
            )

        self.query_one("#cp_hex_input", Input).value = hex_str

    # ── Hex input ────────────────────────────────────────────

    def _apply_hex(self) -> None:
        raw = self.query_one("#cp_hex_input", Input).value.strip()
        try:
            color = Color.parse(raw)
        except Exception:
            self.notify(f"Invalid color: {raw}", severity="error")
            return
        r, g, b = color.rgb
        h, s, l = color.hsl
        if self._mode == "hsl":
            self._values = [int(round(h)), int(round(s * 100)), int(round(l * 100))]
        else:
            self._values = [r, g, b]
        self._refresh_cells()
        self._update_preview()

    # ── Save ─────────────────────────────────────────────────

    # ── Button / input handlers ──────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cp_hex_set":
            self._apply_hex()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cp_hex_input":
            self._apply_hex()
