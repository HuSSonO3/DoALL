"""Recipe modals — edit and delete confirmation."""

import os

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Input, TextArea, Button
from textual.containers import Container, Horizontal, Vertical, VerticalScroll

from .tags import ALL_TAGS, RECIPE_TAG_GROUPS
from .storage import save_recipe


class RecipeEditModal(ModalScreen):
    def __init__(self, recipe: dict):
        super().__init__()
        self._recipe = recipe
        self._selected_tags: set[str] = set(
            t.strip().lower() for t in (recipe.get("tags", "") or "").split(",")
            if t.strip() and t.strip().lower() in ALL_TAGS
        )

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="rm_edit_container"):
            yield Label(f"[bold]Edit: {self._recipe.get('title', 'Recipe')}[/]", id="rm_edit_title")

            yield Label("Title", classes="rm_field_label")
            yield Input(value=self._recipe.get("title", ""), id="rm_edit_title_input")

            with Horizontal(classes="rm_meta_row"):
                yield Input(value=self._recipe.get("time", ""), placeholder="Time", id="rm_edit_time")
                yield Input(value=self._recipe.get("servings", ""), placeholder="Servings", id="rm_edit_servings")

            yield Label("Ingredients", classes="rm_field_label")
            yield TextArea(id="rm_edit_ingredients")

            yield Label("Instructions", classes="rm_field_label")
            yield TextArea(id="rm_edit_instructions")

            yield Label("Tags (click to toggle)", classes="rm_field_label")
            with Vertical(id="rm_edit_tags_container"):
                for group, tags in RECIPE_TAG_GROUPS.items():
                    yield Label(f"[dim]{group}[/]", classes="rm_tag_group_label")
                    with Horizontal(classes="rm_tag_row"):
                        for name in tags:
                            yield Button(name, id=f"rm_etag_{name}")

            with Horizontal(id="rm_edit_buttons"):
                yield Button("Save", variant="primary", id="rm_edit_save")
            yield Label("Press Escape to close", id="rm_small_label")

    def on_mount(self):
        ta = self.query_one("#rm_edit_ingredients", TextArea)
        ta.text = self._recipe.get("ingredients", "")
        ta = self.query_one("#rm_edit_instructions", TextArea)
        ta.text = self._recipe.get("instructions", "")
        self._update_tag_buttons()

    def _update_tag_buttons(self):
        for name in ALL_TAGS:
            btn = self.query_one(f"#rm_etag_{name}", Button)
            btn.variant = "primary" if name in self._selected_tags else "default"

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid and pid.startswith("rm_etag_"):
            tag = pid[len("rm_etag_"):]
            if tag in self._selected_tags:
                self._selected_tags.discard(tag)
            else:
                self._selected_tags.add(tag)
            self._update_tag_buttons()
        elif pid == "rm_edit_save":
            self._save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)

    def _save(self):
        title = self.query_one("#rm_edit_title_input", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return
        if not self._selected_tags:
            self.notify("Please select at least one tag.", severity="error")
            return

        ingredients = self.query_one("#rm_edit_ingredients", TextArea).text
        instructions = self.query_one("#rm_edit_instructions", TextArea).text
        total_time = self.query_one("#rm_edit_time", Input).value.strip()
        servings = self.query_one("#rm_edit_servings", Input).value.strip()
        tags = ", ".join(sorted(self._selected_tags))
        source = self._recipe.get("source", "")

        old_path = self._recipe.get("path", "")
        new_path = save_recipe(title, ingredients, instructions,
                              tags=tags, total_time=total_time,
                              servings=servings, source=source)
        if old_path and os.path.abspath(old_path) != os.path.abspath(new_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

        self.dismiss(True)


class RecipeDeleteModal(ModalScreen):
    def __init__(self, title: str):
        super().__init__()
        self._recipe_title = title

    def compose(self) -> ComposeResult:
        with Container(id="rm_del_container"):
            yield Label(
                f"Delete [bold]{self._recipe_title}[/]?\nThis cannot be undone.",
                id="rm_del_label",
            )
            with Horizontal(id="rm_del_buttons"):
                yield Button("Delete", variant="error", id="rm_del_confirm")
            yield Label("Press Escape to close", id="rm_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "rm_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)
