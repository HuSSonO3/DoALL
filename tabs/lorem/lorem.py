from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Select, TabPane
from textual.widget import Widget
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
import random

WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud",
    "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea",
    "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit",
    "voluptate", "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla",
    "pariatur", "excepteur", "sint", "occaecat", "cupidatat", "non", "proident",
    "sunt", "in", "culpa", "qui", "officia", "deserunt", "mollit", "anim", "id",
    "est", "laborum", "praesent", "sapien", "gravida", "vivamus", "tincidunt",
    "ornare", "facilisis", "cursus", "lacinia", "tellus", "rutrum", "auctor",
    "fermentum", "pharetra", "vehicula", "blandit", "porttitor", "malesuada",
    "suscipit", "ultricies", "dignissim", "imperdiet", "fringilla", "maximus",
    "feugiat", "sagittis", "potenti", "nunc", "morbi", "lectus", "hendrerit",
    "efficitur", "molestie", "convallis", "posuere", "habitasse", "platea",
    "dictumst", "maecenas", "accumsan", "laoreet", "tempus", "scelerisque",
]


def _sentence() -> str:
    count = random.randint(5, 14)
    words = [random.choice(WORDS) for _ in range(count)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def _paragraph() -> str:
    count = random.randint(3, 7)
    return " ".join(_sentence() for _ in range(count))


def generate(kind: str, count: int) -> str:
    if kind == "words":
        words = [random.choice(WORDS) for _ in range(count)]
        return " ".join(words)
    elif kind == "sentences":
        return " ".join(_sentence() for _ in range(count))
    else:
        return "\n\n".join(_paragraph() for _ in range(count))


class LoremWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("g", "generate", "Generate"),
        Binding("s", "save", "Copy to File"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Type:"),
                Select(
                    [("Paragraphs", "paragraphs"),
                     ("Sentences", "sentences"),
                     ("Words", "words")],
                    value="paragraphs",
                    id="lorem_type",
                    allow_blank=False,
                ),
                Label("Count:"),
                Input(value="3", id="lorem_count"),
                Button("Generate", id="lorem_gen", variant="primary"),
                id="lorem_toolbar",
            ),
            RichLog(id="lorem_output", markup=False, wrap=True),
            Horizontal(
                Button("Copy to File", id="lorem_save"),
                id="lorem_bottom",
            ),
            id="lorem_container",
        )

    def on_mount(self) -> None:
        self.query_one("#lorem_gen", Button).press()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "lorem_count":
            self.action_generate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lorem_gen":
            self.action_generate()
        elif event.button.id == "lorem_save":
            self.action_save()

    def action_generate(self) -> None:
        kind = self.query_one("#lorem_type", Select).value
        raw = self.query_one("#lorem_count", Input).value.strip()
        try:
            count = int(raw)
        except ValueError:
            self.notify("Count must be a number.", severity="error")
            return
        count = max(1, min(count, 100))
        text = generate(kind, count)

        output = self.query_one("#lorem_output", RichLog)
        output.clear()
        output.write(text)
        self._last_text = text

    def action_save(self) -> None:
        if not hasattr(self, "_last_text") or not self._last_text:
            self.notify("Nothing to save. Generate first.", severity="warning")
            return
        import os
        from shared import data_root
        out_dir = os.path.join(data_root(), "file_holders", "lorem")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "output.txt")
        with open(path, "w") as f:
            f.write(self._last_text)
        lines = self._last_text.count("\n") + 1
        self.notify(f"Saved to {path} ({lines} lines).")


class LoremTab(TabPane):

    def compose(self) -> ComposeResult:
        yield LoremWidget()
