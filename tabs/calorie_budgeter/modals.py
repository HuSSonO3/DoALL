"""Calorie Budgeter — Modal screens."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

# ═══════════════════════════════════════════════════════════════
# Profile Setup Modal
# ═══════════════════════════════════════════════════════════════

GENDER_OPTIONS = [("Male", "male"), ("Female", "female")]
ACTIVITY_OPTIONS = [
    ("Sedentary (desk job, no exercise)", "sedentary"),
    ("Lightly active (1–3 days/week)", "light"),
    ("Moderately active (3–5 days/week)", "moderate"),
    ("Very active (6–7 days/week)", "active"),
    ("Extra active (physical job + training)", "very_active"),
]
GOAL_OPTIONS = [
    ("0.25 kg / week (slow cut)", "0.25"),
    ("0.5 kg / week (standard cut)", "0.5"),
    ("0.75 kg / week (aggressive)", "0.75"),
    ("1.0 kg / week (max cut)", "1.0"),
]


class ProfileSetupModal(ModalScreen):
    """Set up or edit the user's physical profile for calorie calculations."""

    def __init__(self, profile: dict | None = None):
        super().__init__()
        self._profile = profile or {}

    def compose(self) -> ComposeResult:
        p = self._profile
        with Container(id="cb_profile_container"):
            yield Label("[bold]Profile Setup[/]", id="cb_profile_title")
            yield Label("Weight (kg)", classes="cb_profile_field_label")
            yield Input(
                placeholder="e.g. 80",
                value=str(p.get("weight", "")),
                id="cb_profile_weight",
            )
            yield Label("Height (cm)", classes="cb_profile_field_label")
            yield Input(
                placeholder="e.g. 175",
                value=str(p.get("height", "")),
                id="cb_profile_height",
            )
            yield Label("Age", classes="cb_profile_field_label")
            yield Input(
                placeholder="e.g. 28",
                value=str(p.get("age", "")),
                id="cb_profile_age",
            )
            yield Label("Gender", classes="cb_profile_field_label")
            yield Select(
                GENDER_OPTIONS,
                allow_blank=True,
                id="cb_profile_gender",
                **(({"value": p["gender"]}) if "gender" in p else {}),
            )
            yield Label("Activity Level", classes="cb_profile_field_label")
            yield Select(
                ACTIVITY_OPTIONS,
                allow_blank=True,
                id="cb_profile_activity",
                **(({"value": p["activity"]}) if "activity" in p else {}),
            )
            yield Label("Weekly Loss Goal", classes="cb_profile_field_label")
            yield Select(
                GOAL_OPTIONS,
                allow_blank=True,
                id="cb_profile_goal",
                **(
                    ({"value": str(p["goal_kg_per_week"])})
                    if "goal_kg_per_week" in p
                    else {}
                ),
            )
            with Horizontal(id="cb_profile_buttons"):
                yield Button("Save", variant="primary", id="cb_profile_save")
            yield Label(
                "Press Escape to close",
                id="cb_profile_escape_hint",
            )

    def _try_save(self):
        weight_str = self.query_one("#cb_profile_weight", Input).value.strip()
        height_str = self.query_one("#cb_profile_height", Input).value.strip()
        age_str = self.query_one("#cb_profile_age", Input).value.strip()
        gender_sel = self.query_one("#cb_profile_gender", Select)
        activity_sel = self.query_one("#cb_profile_activity", Select)
        goal_sel = self.query_one("#cb_profile_goal", Select)

        # Validate
        try:
            weight = float(weight_str)
            height = float(height_str)
            age = int(age_str)
            assert weight > 0 and height > 0 and age > 0
        except (ValueError, AssertionError):
            self.notify("Enter valid weight, height, and age.", severity="error")
            return

        if gender_sel.value is Select.BLANK:
            self.notify("Please select a gender.", severity="error")
            return
        if activity_sel.value is Select.BLANK:
            self.notify("Please select an activity level.", severity="error")
            return
        if goal_sel.value is Select.BLANK:
            self.notify("Please select a weekly goal.", severity="error")
            return

        self.dismiss(
            {
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender_sel.value,
                "activity": activity_sel.value,
                "goal_kg_per_week": float(goal_sel.value),
            }
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cb_profile_save":
            self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


# ═══════════════════════════════════════════════════════════════
# Delete Log Entry Modal
# ═══════════════════════════════════════════════════════════════


class DeleteLogModal(ModalScreen):
    """Confirm deletion of a log entry."""

    def __init__(self, label: str, calories: int):
        super().__init__()
        self._label = label
        self._calories = calories

    def compose(self) -> ComposeResult:
        with Container(id="cb_del_container"):
            yield Label(
                f'Delete "[bold]{self._label}[/]" ({self._calories} kcal)?',
                id="cb_del_label",
            )
            with Horizontal(id="cb_del_buttons"):
                yield Button("Delete", variant="error", id="cb_del_confirm")
            yield Label(
                "Press Escape to close",
                id="cb_del_escape_hint",
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cb_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)
