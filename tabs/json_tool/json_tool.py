from textual.app import ComposeResult
from textual.widgets import Button, Label, RichLog, TabPane, TextArea
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
import base64
import json
import os


class JsonToolWidget(Widget, can_focus=True):
    """Paste JSON → pretty-print, minify, validate, copy output."""

    BINDINGS = [
        Binding("p", "pretty", "Pretty"),
        Binding("m", "minify", "Minify"),
        Binding("v", "validate", "Validate"),
        Binding("s", "save", "Save"),
        Binding("c", "clear", "Clear"),
    ]

    def __init__(self):
        super().__init__()
        self._last_output = ""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Button("Pretty", id="json_pretty", variant="primary"),
                Button("Minify", id="json_minify"),
                Button("Validate", id="json_validate"),
                Button("Save", id="json_save"),
                Button("Clear", id="json_clear"),
                id="json_toolbar",
            ),
            Horizontal(
                Vertical(
                    Label("Input", id="json_label_input"),
                    TextArea(id="json_input"),
                    id="json_input_pane",
                ),
                Vertical(
                    Label("Output", id="json_label_output"),
                    RichLog(id="json_output", highlight=True, markup=True, wrap=True),
                    id="json_output_pane",
                ),
                id="json_panes",
            ),
            id="json_container",
        )

    def on_mount(self) -> None:
        self.query_one("#json_input", TextArea).focus()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "json_pretty":
            self.action_pretty()
        elif bid == "json_minify":
            self.action_minify()
        elif bid == "json_validate":
            self.action_validate()
        elif bid == "json_save":
            self.action_save()
        elif bid == "json_clear":
            self.action_clear()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_pretty(self) -> None:
        text = self.query_one("#json_input", TextArea).text
        if not text.strip():
            self._show_output("", "[dim]Input is empty.[/]")
            return
        try:
            obj = json.loads(text)
            result = json.dumps(obj, indent=2, ensure_ascii=False)
            self._show_output(result, result)
        except json.JSONDecodeError as e:
            self._show_error(e, text)

    def action_minify(self) -> None:
        text = self.query_one("#json_input", TextArea).text
        if not text.strip():
            self._show_output("", "[dim]Input is empty.[/]")
            return
        try:
            obj = json.loads(text)
            result = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
            self._show_output(result, result)
        except json.JSONDecodeError as e:
            self._show_error(e, text)

    def action_validate(self) -> None:
        text = self.query_one("#json_input", TextArea).text
        if not text.strip():
            self._show_output("", "[dim]Input is empty.[/]")
            return
        try:
            obj = json.loads(text)
            kinds = {dict: "object", list: "array", str: "string",
                     int: "number", float: "number", bool: "boolean", type(None): "null"}
            kind = kinds.get(type(obj), type(obj).__name__)
            size = len(text.encode("utf-8"))
            nested = self._max_depth(obj)
            msg = (
                f"[bold green]✓ Valid JSON[/]\n\n"
                f"  Root type:  [bold]{kind}[/]\n"
                f"  Size:       {size:,} bytes\n"
                f"  Max depth:  {nested}"
            )
            if isinstance(obj, dict):
                msg += f"\n  Top keys:   {len(obj)} ({', '.join(list(obj.keys())[:10])}{'...' if len(obj) > 10 else ''})"
            elif isinstance(obj, list):
                msg += f"\n  Items:      {len(obj)}"
            self._show_output(text, msg)  # plain fallback for copy = original input
        except json.JSONDecodeError as e:
            self._show_error(e, text)

    def action_save(self) -> None:
        if not self._last_output:
            self.notify("Nothing to copy.", severity="warning")
            return

        from shared import data_root
        out_dir = os.path.join(data_root(), "file_holders", "json_tool")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "output.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._last_output)
        except Exception:
            self.notify("Failed to write file.", severity="error")
            return

        # Best-effort OSC 52 (works in many modern terminals)
        self._osc52_copy(self._last_output)

        lines = self._last_output.count("\n") + 1
        size = len(self._last_output)
        self.notify(
            f"Saved to {path} ({lines} lines, {size}B).",
        )

    def action_clear(self) -> None:
        self.query_one("#json_input", TextArea).text = ""
        self._show_output("", "")

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _show_output(self, plain: str, display: str) -> None:
        self._last_output = plain
        output = self.query_one("#json_output", RichLog)
        output.clear()
        output.write(display)

    def _show_error(self, exc: json.JSONDecodeError, raw: str) -> None:
        line = exc.lineno
        col = exc.colno
        raw_lines = raw.splitlines()
        out_lines = [f"[bold red]✗ Invalid JSON[/] at line {line}, column {col}"]
        out_lines.append(f"[red]{exc.msg}[/]")
        out_lines.append("")
        start = max(0, line - 2)
        end = min(len(raw_lines), line + 1)
        for i in range(start, end):
            prefix = " → " if i == line - 1 else "   "
            ln = f"{i + 1:>4} {prefix}{raw_lines[i]}"
            if i == line - 1:
                ln = f"[red]{ln}[/]"
            else:
                ln = f"[dim]{ln}[/]"
            out_lines.append(ln)
            if i == line - 1 and col and col <= len(raw_lines[i]) + 1:
                pointer = " " * (7 + col) + "^"
                out_lines.append(f"[yellow]{pointer}[/]")
        self._show_output("", "\n".join(out_lines))

    # ------------------------------------------------------------------
    # Clipboard (OSC 52 — works in most modern terminals, no deps)
    # ------------------------------------------------------------------

    @staticmethod
    def _osc52_copy(text: str) -> None:
        """Best-effort clipboard copy via OSC 52 (silent no-op if unsupported)."""
        try:
            encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
            # Split into chunks — some terminals limit OSC 52 to ~4096 bytes
            chunk = 3072
            for i in range(0, len(encoded), chunk):
                print(f"\x1b]52;c;{encoded[i:i+chunk]}\x07", end="", flush=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _max_depth(obj, current=0):
        if isinstance(obj, dict):
            if not obj:
                return current + 1
            return max(JsonToolWidget._max_depth(v, current + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current + 1
            return max(JsonToolWidget._max_depth(v, current + 1) for v in obj)
        return current


# ---------------------------------------------------------------------------
# TabPane wrapper
# ---------------------------------------------------------------------------

class JsonToolTab(TabPane):
    """TabPane wrapper for the JSON Tool module."""

    def compose(self) -> ComposeResult:
        yield JsonToolWidget()
