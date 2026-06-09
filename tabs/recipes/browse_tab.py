"""Browse Recipes tab — search, filter, view, edit, and delete saved recipes."""

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, TextArea, DataTable, Button, Select
from textual.containers import Horizontal, Vertical, VerticalScroll

from .tags import RECIPE_TAG_GROUPS
from .storage import parse_saved_recipe, load_all_recipes
from .modals import RecipeEditModal, RecipeDeleteModal


class BrowseRecipesTab(TabPane):

    def __init__(self, title="My Recipes", **kwargs):
        super().__init__(title, **kwargs)
        self._selected_path: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="rm_browse_container"):
            yield Label("[bold $accent]My Recipes[/]", id="rm_browse_title")

            with Horizontal(id="rm_search_row"):
                yield Input(placeholder="Search recipes...", id="rm_search")
                yield Select(
                    [("All Recipes", "")] +
                    [(f"[dim]{group}[/] — {name}", name)
                     for group, tags in RECIPE_TAG_GROUPS.items()
                     for name in tags],
                    value="", allow_blank=False, id="rm_tag_filter",
                )

            yield DataTable(id="rm_recipe_list")

            # ── Detail view ───────────────────────────────────
            with VerticalScroll(id="rm_detail"):
                yield Label("", id="rm_detail_title")
                with Horizontal(classes="rm_meta_row"):
                    yield Label("", id="rm_detail_time")
                    yield Label("", id="rm_detail_servings")
                    yield Label("", id="rm_detail_tags")

                yield Label("[bold]Ingredients[/]", classes="rm_section_label")
                yield TextArea.code_editor("", id="rm_detail_ingredients", read_only=True)

                yield Label("[bold]Instructions[/]", classes="rm_section_label")
                yield TextArea.code_editor("", id="rm_detail_instructions", read_only=True)

                with Horizontal(id="rm_detail_actions"):
                    yield Button("Edit", variant="primary", id="rm_edit_btn")
                    yield Button("Delete", variant="error", id="rm_delete_btn")

    def on_mount(self):
        table = self.query_one("#rm_recipe_list", DataTable)
        table.add_columns("Title", "Tags", "Time")
        table.cursor_type = "row"

        for wid in ("#rm_detail_ingredients", "#rm_detail_instructions"):
            ta = self.query_one(wid, TextArea)
            ta.show_line_numbers = False
            ta.soft_wrap = True

        self._refresh_list()

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "rm_tag_filter":
            self._refresh_list()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "rm_search":
            self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "rm_edit_btn":
            event.stop()
            self._edit_recipe()
        elif pid == "rm_delete_btn":
            event.stop()
            self._delete_recipe()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id != "rm_recipe_list":
            return
        row_key = event.row_key.value
        self._selected_path = row_key
        self._show_detail(row_key)

    def _edit_recipe(self):
        if not self._selected_path:
            return
        recipe = parse_saved_recipe(Path(self._selected_path))
        if not recipe:
            return
        self.app.push_screen(RecipeEditModal(recipe), self._on_edit_saved)

    def _delete_recipe(self):
        if not self._selected_path:
            return
        recipe = parse_saved_recipe(Path(self._selected_path))
        title = recipe.get("title", "this recipe") if recipe else "this recipe"
        self.app.push_screen(RecipeDeleteModal(title), self._on_delete)

    def _on_edit_saved(self, result):
        self._selected_path = None
        self._clear_detail()
        self._refresh_list()

    def _on_delete(self, confirmed: bool):
        if not confirmed or not self._selected_path:
            return
        try:
            os.remove(self._selected_path)
        except OSError:
            pass
        self._selected_path = None
        self._clear_detail()
        self._refresh_list()

    def _refresh_list(self):
        search = self.query_one("#rm_search", Input).value.strip().lower()
        tag_filter = self.query_one("#rm_tag_filter", Select).value
        table = self.query_one("#rm_recipe_list", DataTable)
        table.clear()

        recipes = load_all_recipes()
        for r in recipes:
            title = r.get("title", "")
            tags = r.get("tags", "")
            if search:
                if search not in title.lower() and search not in tags.lower():
                    continue
            if tag_filter:
                recipe_tags = set(t.strip().lower() for t in tags.split(","))
                if tag_filter not in recipe_tags:
                    continue
            table.add_row(
                title,
                tags,
                r.get("time", ""),
                key=r["path"],
            )

    def _clear_detail(self):
        self.query_one("#rm_detail_title", Label).update("")
        self.query_one("#rm_detail_time", Label).update("")
        self.query_one("#rm_detail_servings", Label).update("")
        self.query_one("#rm_detail_tags", Label).update("")
        self.query_one("#rm_detail_ingredients", TextArea).text = ""
        self.query_one("#rm_detail_instructions", TextArea).text = ""

    def _show_detail(self, path: str):
        recipe = parse_saved_recipe(Path(path))
        if not recipe:
            return

        self.query_one("#rm_detail_title", Label).update(
            f"[bold $accent]{recipe.get('title', '')}[/]"
        )
        parts = []
        if recipe.get("time"):
            parts.append(f"⏱ {recipe['time']}")
        if recipe.get("servings"):
            parts.append(f"🍽 {recipe['servings']}")
        self.query_one("#rm_detail_time", Label).update("  ".join(parts))
        self.query_one("#rm_detail_servings", Label).update(
            f"[dim]{recipe.get('source', '')}[/]" if recipe.get("source") else ""
        )
        self.query_one("#rm_detail_tags", Label).update(
            f"[dim]{recipe.get('tags', '')}[/]"
        )

        self.query_one("#rm_detail_ingredients", TextArea).text = (
            recipe.get("ingredients", "")
        )
        self.query_one("#rm_detail_instructions", TextArea).text = (
            recipe.get("instructions", "")
        )
