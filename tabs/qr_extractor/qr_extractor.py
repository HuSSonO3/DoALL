"""QR Generator & Extractor — widget and tab."""

import os
import re
import secrets
from datetime import date

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, TextArea, DataTable, Button
from textual.widget import Widget
from textual.containers import Horizontal, Vertical

from .parser import generate_qr_ascii, generate_qr_svg, parse_payload


class QRToolWidget(Widget):

    SAVE_DIR = "file_holders/qr_codes"

    def compose(self) -> ComposeResult:
        with Vertical(id="qr_container"):
            yield Label("[bold]QR Generator & Extractor[/]", id="qr_title")

            # ── Generate ──────────────────────────────────────
            with Vertical(id="qr_gen_section"):
                yield Label("[bold $accent]── Generate[/]", id="qr_gen_heading")
                with Horizontal(id="qr_gen_row"):
                    yield Input(
                        placeholder="Text, URL, or data to encode...",
                        id="qr_gen_input",
                    )
                    yield Button("Generate", variant="primary", id="qr_gen_btn")
                    yield Button("Clear", id="qr_gen_clear")
                yield TextArea.code_editor("", id="qr_gen_output", read_only=True)
                with Horizontal(id="qr_gen_save_row"):
                    yield Button("Save to File", id="qr_gen_save")
                yield Label("", id="qr_gen_save_label")

            # ── Extract ───────────────────────────────────────
            with Vertical(id="qr_ext_section"):
                yield Label("[bold $accent]── Extract (paste payload)[/]", id="qr_ext_heading")
                with Horizontal(id="qr_ext_input_row"):
                    yield TextArea.code_editor("", id="qr_ext_input")
                    yield Button("Clear", id="qr_ext_clear")
                yield Label("", id="qr_ext_type_label")
                yield DataTable(id="qr_ext_results")

    def on_mount(self):
        self.query_one("#qr_gen_input", Input).focus()
        gen_out = self.query_one("#qr_gen_output", TextArea)
        gen_out.show_line_numbers = False
        table = self.query_one("#qr_ext_results", DataTable)
        table.add_columns("Field", "Value")
        table.cursor_type = "row"
        self._parse_timer = None

    # ── Generate handlers ────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "qr_gen_input":
            self._generate()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "qr_gen_btn":
            self._generate()
        elif pid == "qr_gen_clear":
            self.query_one("#qr_gen_input", Input).value = ""
            self.query_one("#qr_gen_output", TextArea).text = ""
            self.query_one("#qr_gen_save_label", Label).update("")
            self.query_one("#qr_gen_input", Input).focus()
        elif pid == "qr_gen_save":
            self._save()
        elif pid == "qr_ext_clear":
            self.query_one("#qr_ext_input", TextArea).text = ""
            self.query_one("#qr_ext_type_label", Label).update("")
            self.query_one("#qr_ext_results", DataTable).clear()

    def _generate(self):
        text = self.query_one("#qr_gen_input", Input).value.strip()
        output = self.query_one("#qr_gen_output", TextArea)
        if not text:
            output.text = "[Enter text and click Generate to create a QR code]"
            return
        try:
            output.text = generate_qr_ascii(text)
        except Exception as e:
            output.text = f"[Error generating QR: {e}]"

    def _save(self):
        content = self.query_one("#qr_gen_input", Input).value.strip()
        label = self.query_one("#qr_gen_save_label", Label)
        if not content:
            label.update("[bold red]Nothing to save[/]")
            return
        try:
            svg = generate_qr_svg(content)
        except Exception as e:
            label.update(f"[bold red]Error: {e}[/]")
            return

        today = date.today().isoformat()
        slug = re.sub(r"[^a-zA-Z0-9_-]", "", content)[:20].strip("_-") or "qr"
        suffix = secrets.token_hex(3)
        filename = f"qr_{today}_{slug}_{suffix}.svg"

        os.makedirs(self.SAVE_DIR, exist_ok=True)
        path = os.path.join(self.SAVE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)

        label.update(f"[dim]Saved to:[/] {os.path.abspath(path)}")

    # ── Extract handlers ─────────────────────────────────────

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id == "qr_ext_input":
            if self._parse_timer:
                self._parse_timer.stop()
            self._parse_timer = self.set_timer(0.3, self._extract_update)

    def _extract_update(self):
        raw = self.query_one("#qr_ext_input", TextArea).text
        if not raw.strip():
            self.query_one("#qr_ext_type_label", Label).update("")
            self.query_one("#qr_ext_results", DataTable).clear()
            return
        label, rows = parse_payload(raw)
        self.query_one("#qr_ext_type_label", Label).update(
            f"[bold $accent]Detected:[/] {label}"
        )
        table = self.query_one("#qr_ext_results", DataTable)
        table.clear()
        for field, value in rows:
            table.add_row(field, value)


class QRToolTab(TabPane):
    def compose(self) -> ComposeResult:
        yield QRToolWidget()
