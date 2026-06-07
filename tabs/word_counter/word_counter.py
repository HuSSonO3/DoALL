import re
from collections import Counter

from textual.app import ComposeResult
from textual.widgets import TabPane, Label, DataTable, TextArea, Button
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical


class WordCounterWidget(Widget):

    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "i", "you", "he",
        "she", "it", "we", "they", "me", "him", "her", "us", "them", "my",
        "your", "his", "its", "our", "their", "this", "that", "these", "those",
        "not", "no", "so", "if", "as", "than", "too", "very", "just", "about",
        "also", "into", "over", "after", "before", "between", "under", "up",
        "out", "down", "off", "here", "there", "when", "where", "how", "all",
        "each", "every", "both", "few", "more", "most", "other", "some", "such",
        "only", "own", "same", "then", "now",
    }

    def compose(self) -> ComposeResult:
        with Vertical(id="wc_container"):
            yield Label("[bold]Word Counter[/]", id="wc_title")

            yield TextArea.code_editor("", id="wc_input")

            with Horizontal(id="wc_stats"):
                with Vertical(classes="wc_stat_card"):
                    yield Label("Words", classes="wc_stat_label")
                    yield Label("0", classes="wc_stat_value", id="wc_words")
                with Vertical(classes="wc_stat_card"):
                    yield Label("Characters", classes="wc_stat_label")
                    yield Label("0", classes="wc_stat_value", id="wc_chars")
                with Vertical(classes="wc_stat_card"):
                    yield Label("No Spaces", classes="wc_stat_label")
                    yield Label("0", classes="wc_stat_value", id="wc_chars_ns")
                with Vertical(classes="wc_stat_card"):
                    yield Label("Lines", classes="wc_stat_label")
                    yield Label("0", classes="wc_stat_value", id="wc_lines")
                with Vertical(classes="wc_stat_card"):
                    yield Label("Paragraphs", classes="wc_stat_label")
                    yield Label("0", classes="wc_stat_value", id="wc_paras")
                with Vertical(classes="wc_stat_card"):
                    yield Label("Reading Time", classes="wc_stat_label")
                    yield Label("0m", classes="wc_stat_value", id="wc_read")
                    yield Label("[dim]200 wpm[/]", classes="wc_stat_note")

            with Horizontal(id="wc_actions"):
                yield Button("Clear", id="wc_clear_btn")

            yield Label("Top Keywords", id="wc_kw_heading")
            yield DataTable(id="wc_keywords")

    def on_mount(self):
        self.query_one("#wc_input", TextArea).focus()
        table = self.query_one("#wc_keywords", DataTable)
        table.add_columns("#", "Word", "Count")
        table.cursor_type = "row"
        self._parse_timer = None

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id == "wc_input":
            if self._parse_timer:
                self._parse_timer.stop()
            self._parse_timer = self.set_timer(0.3, self._update)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "wc_clear_btn":
            self.query_one("#wc_input", TextArea).text = ""
            self._update()

    def _update(self):
        text = self.query_one("#wc_input", TextArea).text

        # Counts
        words = re.findall(r"[a-zA-Z]+", text)
        word_count = len(words)
        char_count = len(text)
        char_ns = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        lines = text.count("\n") + (1 if text else 0)
        paras = len([p for p in re.split(r"\n\s*\n", text) if p.strip()])

        # Reading time (avg 200 wpm)
        mins = max(1, round(word_count / 200)) if word_count > 0 else 0

        self.query_one("#wc_words", Label).update(str(word_count))
        self.query_one("#wc_chars", Label).update(str(char_count))
        self.query_one("#wc_chars_ns", Label).update(str(char_ns))
        self.query_one("#wc_lines", Label).update(str(lines))
        self.query_one("#wc_paras", Label).update(str(paras))
        self.query_one("#wc_read", Label).update(f"{mins}m" if mins else "0m")

        # Keywords (exclude stop words, min 3 chars, lowercase)
        filtered = [w.lower() for w in words if w.lower() not in self.STOP_WORDS and len(w) >= 3]
        top = Counter(filtered).most_common(20)

        table = self.query_one("#wc_keywords", DataTable)
        table.clear()
        for i, (word, count) in enumerate(top, 1):
            table.add_row(str(i), word, str(count))


class WordCounterTab(TabPane):
    def compose(self) -> ComposeResult:
        yield WordCounterWidget()
