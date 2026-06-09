"""Gitignore Builder — widget and tab."""

import os
import re

from textual.app import ComposeResult
from textual.widgets import TabPane, Label, TextArea, Button
from textual.widget import Widget
from textual.containers import Horizontal, Vertical

from .templates import TEMPLATES, TEMPLATE_NAMES


class GitignoreWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected: set[str] = set()

    def compose(self) -> ComposeResult:
        with Vertical(id="gi_container"):
            yield Label("[bold]Gitignore Builder[/]", id="gi_title")
            yield Label("[dim]Click a template to toggle it on/off[/]", id="gi_hint")

            with Vertical(id="gi_template_grid"):
                for i, name in enumerate(TEMPLATE_NAMES):
                    yield Button(name, id=f"gi_tpl_{i}")

            with Horizontal(id="gi_actions"):
                yield Button("Select All", id="gi_select_all")
                yield Button("Deselect All", id="gi_deselect_all")
                yield Button("Generate", variant="primary", id="gi_generate")

            yield TextArea.code_editor("", id="gi_output", read_only=True)

            with Horizontal(id="gi_save_row"):
                yield Button("Save to File", id="gi_save_btn")
            yield Label("", id="gi_save_label")

    def on_mount(self):
        self._update_button_styles()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id

        if pid and pid.startswith("gi_tpl_"):
            idx = int(pid.split("_")[-1])
            name = TEMPLATE_NAMES[idx]
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
            self._update_button_styles()

        elif pid == "gi_select_all":
            self._selected = set(TEMPLATE_NAMES)
            self._update_button_styles()

        elif pid == "gi_deselect_all":
            self._selected.clear()
            self._update_button_styles()

        elif pid == "gi_generate":
            self._generate()
        elif pid == "gi_save_btn":
            self._save()

    def _update_button_styles(self):
        for i, name in enumerate(TEMPLATE_NAMES):
            btn = self.query_one(f"#gi_tpl_{i}", Button)
            btn.variant = "primary" if name in self._selected else "default"
        count = len(self._selected)
        self.query_one("#gi_hint", Label).update(
            f"[dim]{count} template{'s' if count != 1 else ''} selected[/]"
            if count else "[dim]Click a template to toggle it on/off[/]"
        )

    def _generate(self):
        output = self.query_one("#gi_output", TextArea)
        if not self._selected:
            output.text = "# Select at least one template and click Generate\n"
            return
        lines = ["# Generated .gitignore", "#"]
        for name in sorted(self._selected, key=lambda n: TEMPLATE_NAMES.index(n)):
            lines.append(f"# ── {name} ──")
            lines.append(TEMPLATES[name].rstrip("\n"))
            lines.append("")
        output.text = "\n".join(lines)

    SAVE_DIR = "file_holders/gitignore"

    def _save(self):
        content = self.query_one("#gi_output", TextArea).text
        label = self.query_one("#gi_save_label", Label)

        if not content.strip():
            label.update("[bold red]Generate a .gitignore first[/]")
            return

        slug = "_".join(
            re.sub(r"[^a-z0-9]+", "", name.lower())
            for name in sorted(self._selected)
        )[:60] or "gitignore"

        os.makedirs(self.SAVE_DIR, exist_ok=True)

        # Save the actual dotfile (hidden — use ls -la to see it)
        dotfile = os.path.join(self.SAVE_DIR, f".gitignore_{slug}")
        with open(dotfile, "w", encoding="utf-8") as f:
            f.write(content)

        # Also save a visible .txt copy
        txtfile = os.path.join(self.SAVE_DIR, f"gitignore_{slug}.txt")
        with open(txtfile, "w", encoding="utf-8") as f:
            f.write(content)

        label.update(
            f"[dim]Saved:[/] {os.path.abspath(dotfile)}\n"
            f"[dim]Also:[/] {os.path.abspath(txtfile)}\n"
            f"[dim]Dotfiles are hidden — use [bold]ls -la[/] or rename the .txt[/]"
        )


class GitignoreBuilderTab(TabPane):
    def compose(self) -> ComposeResult:
        yield GitignoreWidget()
