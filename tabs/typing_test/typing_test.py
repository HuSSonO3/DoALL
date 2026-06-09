"""Typing Speed Test — measure WPM and accuracy, widget and tab."""

import time
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import TabPane, Label, TextArea, DataTable, Button
from textual.widget import Widget
from textual.containers import Horizontal, Vertical

from .word_pool import random_prompt


class TypingTestWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._start_time: float | None = None
        self._timer_handle = None
        self._finished = False
        self._current_prompt: str = ""
        self._prev_text: str = ""
        self._total_keystrokes: int = 0
        self._error_count: int = 0
        self._history: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="tt_container"):
            yield Label("[bold]Typing Speed Test[/]", id="tt_title")

            with Vertical(id="tt_prompt_card"):
                yield Label("", id="tt_prompt")

            yield TextArea(id="tt_input")

            with Horizontal(id="tt_stats"):
                with Vertical(classes="tt_stat_card"):
                    yield Label("Time", classes="tt_stat_label")
                    yield Label("0.0s", classes="tt_stat_value", id="tt_time")
                with Vertical(classes="tt_stat_card"):
                    yield Label("WPM", classes="tt_stat_label")
                    yield Label("0", classes="tt_stat_value", id="tt_wpm")
                with Vertical(classes="tt_stat_card"):
                    yield Label("Accuracy", classes="tt_stat_label")
                    yield Label("—", classes="tt_stat_value", id="tt_accuracy")

            yield Label("", id="tt_result")

            with Horizontal(id="tt_actions"):
                yield Button("New Text", variant="primary", id="tt_new_btn")
                yield Button("Reset", id="tt_reset_btn")

            yield Label("[bold]History[/]", id="tt_history_heading")
            yield DataTable(id="tt_history")

    def on_mount(self):
        table = self.query_one("#tt_history", DataTable)
        table.add_columns("Date", "WPM", "Acc", "Errors")
        table.cursor_type = "row"
        self._new_prompt()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "tt_new_btn":
            self._new_prompt()
        elif pid == "tt_reset_btn":
            self._reset()

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id != "tt_input":
            return
        if self._finished:
            return

        new_text = self.query_one("#tt_input", TextArea).text
        prompt = self._current_prompt
        prev = self._prev_text

        if not new_text and not prev:
            return

        if self._start_time is None:
            self._start_time = time.monotonic()
            self._timer_handle = self.set_interval(0.1, self._update_stats)

        if len(new_text) > len(prev):
            added = len(new_text) - len(prev)
            self._total_keystrokes += added
            for i, ch in enumerate(new_text):
                if i >= len(prev) or ch != prev[i]:
                    inserted = new_text[i:i + added]
                    for j, c in enumerate(inserted):
                        pos = i + j
                        if pos >= len(prompt) or c != prompt[pos]:
                            self._error_count += 1
                    break
        elif len(new_text) < len(prev):
            removed = len(prev) - len(new_text)
            self._total_keystrokes += removed
            self._error_count += removed

        self._prev_text = new_text

        if len(new_text) >= len(prompt):
            self._finish()

        self._update_stats()

    def _update_stats(self):
        if self._start_time is None:
            return
        elapsed = time.monotonic() - self._start_time
        minutes = elapsed / 60.0
        correct = self._total_keystrokes - self._error_count
        wpm = round((correct / 5) / minutes) if minutes > 0 and correct > 0 else 0
        accuracy = round(correct / self._total_keystrokes * 100) if self._total_keystrokes > 0 else 0

        self.query_one("#tt_time", Label).update(f"{elapsed:.1f}s")
        self.query_one("#tt_wpm", Label).update(str(wpm))
        self.query_one("#tt_accuracy", Label).update(f"{accuracy}%")

    def _finish(self):
        self._finished = True
        if self._timer_handle:
            self._timer_handle.stop()
            self._timer_handle = None

        elapsed = time.monotonic() - self._start_time if self._start_time else 0
        minutes = elapsed / 60.0
        correct = self._total_keystrokes - self._error_count
        wpm = round((correct / 5) / minutes) if minutes > 0 and correct > 0 else 0
        accuracy = round(correct / self._total_keystrokes * 100) if self._total_keystrokes > 0 else 0

        self.query_one("#tt_time", Label).update(f"{elapsed:.1f}s")
        self.query_one("#tt_wpm", Label).update(str(wpm))
        self.query_one("#tt_accuracy", Label).update(f"{accuracy}%")

        if wpm >= 60:
            rating = "[bold green]🔥 Fast![/]"
        elif wpm >= 40:
            rating = "[bold $accent]👍 Good[/]"
        elif wpm >= 20:
            rating = "[dim]🆗 Okay[/]"
        else:
            rating = "[dim]🐢 Keep practicing[/]"

        self.query_one("#tt_result", Label).update(
            f"{rating}  —  [bold]{wpm} WPM[/] at {accuracy}% accuracy, {elapsed:.1f}s"
        )

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "wpm": wpm,
            "accuracy": accuracy,
            "errors": self._error_count,
            "keystrokes": self._total_keystrokes,
        }
        self._history.append(entry)
        self._refresh_history()

    def _new_prompt(self):
        self._current_prompt = random_prompt()
        self.query_one("#tt_prompt", Label).update(self._current_prompt)
        self._reset_state()

    def _reset(self):
        self._reset_state()

    def _reset_state(self):
        if self._timer_handle:
            self._timer_handle.stop()
            self._timer_handle = None
        self._start_time = None
        self._finished = False
        self._prev_text = ""
        self._total_keystrokes = 0
        self._error_count = 0
        self.query_one("#tt_input", TextArea).text = ""
        self.query_one("#tt_input", TextArea).focus()
        self.query_one("#tt_time", Label).update("0.0s")
        self.query_one("#tt_wpm", Label).update("0")
        self.query_one("#tt_accuracy", Label).update("—")
        self.query_one("#tt_result", Label).update("")

    def _refresh_history(self):
        table = self.query_one("#tt_history", DataTable)
        table.clear()
        for entry in reversed(self._history[-15:]):
            table.add_row(
                entry["date"],
                str(entry["wpm"]),
                f"{entry['accuracy']}%",
                str(entry["errors"]),
            )


class TypingTestTab(TabPane):
    def compose(self) -> ComposeResult:
        yield TypingTestWidget()
