import re
from datetime import date
from collections import defaultdict

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, TextArea, Button
from textual.widget import Widget
from textual.containers import Horizontal, Vertical


# ── Classification ────────────────────────────────────────────

# Phase 1: explicit conventional-commit prefixes — checked first, take priority
PREFIXES = [
    ("✨ Features",     r"^feat[(:]"),
    ("🐛 Fixes",        r"^fix[(:]"),
    ("📝 Docs",         r"^docs[(:]"),
    ("♻️ Refactors",    r"^refactor[(:]"),
    ("✅ Tests",        r"^test[(:]"),
    ("💄 Style",        r"^style[(:]"),
    ("⚡ Performance",  r"^perf[(:]"),
    ("📦 Build",        r"^build[(:]"),
    ("🔄 CI",           r"^ci[(:]"),
    ("🔧 Chores",       r"^chore[(:]"),
]

# Phase 2: keyword fallback — only checked when no prefix matched
KEYWORDS = [
    ("✨ Features",     [r"\badd(s|ed|ing)?\b", r"\bnew\b", r"\bintroduce"]),
    ("🐛 Fixes",        [r"\bfix(s|ed|ing)?\b", r"\bbug\b", r"\bresolve", r"\bpatch"]),
    ("📝 Docs",         [r"\bdoc(s|umentation)?\b", r"\breadme\b"]),
    ("♻️ Refactors",    [r"\brefactor", r"\bclean\s?up\b", r"\bsimplif"]),
    ("✅ Tests",        [r"\btest(s|ing)?\b"]),
    ("⚡ Performance",  [r"\bperf(ormance)?\b", r"\bfaster\b", r"\bspeed\b"]),
    ("🔄 CI",           [r"\bci\b", r"\bpipeline\b"]),
    ("🔧 Chores",       [r"\bbump\b", r"\bupdate dep", r"\bdependenc"]),
]


def classify_line(line: str) -> str:
    """Return the category name for a single commit line."""
    lower = line.lower()

    # Phase 1: conventional prefix wins
    for name, pat in PREFIXES:
        if re.search(pat, lower):
            return name

    # Phase 2: keyword fallback
    for name, patterns in KEYWORDS:
        for pat in patterns:
            if re.search(pat, lower):
                return name

    return "📌 Other"


# ── Widget ────────────────────────────────────────────────────

class ChangelogWidget(Widget):

    def compose(self) -> ComposeResult:
        with Vertical(id="cl_container"):
            yield Label("[bold]Changelog Generator[/]", id="cl_title")

            with Horizontal(id="cl_version_row"):
                yield Label("Version:", id="cl_version_label")
                yield Input(
                    placeholder="e.g. v1.3.0",
                    id="cl_version",
                )

            yield TextArea.code_editor(
                "",
                id="cl_input",
            )

            with Horizontal(id="cl_actions"):
                yield Button("Generate", variant="primary", id="cl_generate_btn")
                yield Button("Clear", id="cl_clear_btn")

            yield Label("Output — copy-ready Markdown", id="cl_output_heading")
            yield TextArea.code_editor(
                "",
                id="cl_output",
                read_only=True,
            )

    def on_mount(self):
        self.query_one("#cl_input", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "cl_generate_btn":
            self._generate()
        elif pid == "cl_clear_btn":
            self.query_one("#cl_input", TextArea).text = ""
            self.query_one("#cl_output", TextArea).text = ""

    def _generate(self):
        raw = self.query_one("#cl_input", TextArea).text.strip()
        output = self.query_one("#cl_output", TextArea)

        if not raw:
            output.text = "[No commits to process]"
            return

        version = self.query_one("#cl_version", Input).value.strip()
        if not version:
            version = "Unreleased"

        # Classify each non-blank line
        buckets = defaultdict(list)
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Strip common git log prefixes like "* ", "- ", commit hashes
            clean = re.sub(r"^[a-f0-9]{7,}\s+", "", stripped)   # short hash
            clean = re.sub(r"^[*\-•]\s*", "", clean)             # bullet
            cat = classify_line(clean)
            buckets[cat].append(clean)

        # Build markdown
        today = date.today().isoformat()
        lines = [
            f"## {version} ({today})",
            "",
        ]

        # Order by CATEGORIES ordering, then Other, then any extras
        for name, _ in PREFIXES:
            items = buckets.pop(name, [])
            if not items:
                continue
            lines.append(f"### {name} ({len(items)})")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

        # Any remaining buckets not in our known list
        for cat, items in sorted(buckets.items()):
            if not items:
                continue
            lines.append(f"### {cat} ({len(items)})")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

        output.text = "\n".join(lines)


# ── Tab ───────────────────────────────────────────────────────

class ChangelogTab(TabPane):
    def compose(self) -> ComposeResult:
        yield ChangelogWidget()
