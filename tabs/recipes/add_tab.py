"""Add Recipe tab — scrape from URL or enter manually."""

from recipe_scrapers import scrape_me, NoSchemaFoundInWildMode

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, TextArea, Button
from textual.containers import Horizontal, Vertical, VerticalScroll

from .tags import ALL_TAGS, RECIPE_TAG_GROUPS
from .storage import save_recipe


class AddRecipeTab(TabPane):

    def __init__(self, title="Add Recipe", **kwargs):
        super().__init__(title, **kwargs)
        self._selected_tags: set[str] = set()

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="rm_add_container"):
            yield Label("[bold $accent]Add Recipe[/]", id="rm_add_title")

            # ── URL scrape ────────────────────────────────────
            with Horizontal(id="rm_url_row"):
                yield Input(
                    placeholder="Paste recipe URL to scrape...",
                    id="rm_url",
                )
                yield Button("Scrape", variant="primary", id="rm_scrape_btn")

            yield Label("", id="rm_scrape_status")

            # ── Form ──────────────────────────────────────────
            yield Label("Title", classes="rm_field_label")
            yield Input(placeholder="Recipe title...", id="rm_title_input")

            with Horizontal(classes="rm_meta_row"):
                yield Input(placeholder="Time (e.g. 45 min)", id="rm_time")
                yield Input(placeholder="Servings (e.g. 4)", id="rm_servings")

            yield Label("Ingredients", classes="rm_field_label")
            yield TextArea(id="rm_ingredients")

            yield Label("Instructions", classes="rm_field_label")
            yield TextArea(id="rm_instructions")

            yield Label("Tags (click to toggle)", classes="rm_field_label")
            yield Label("", id="rm_tags_display")
            with Vertical(id="rm_tags_container"):
                for group, tags in RECIPE_TAG_GROUPS.items():
                    yield Label(f"[dim]{group}[/]", classes="rm_tag_group_label")
                    with Horizontal(classes="rm_tag_row"):
                        for name in tags:
                            yield Button(name, id=f"rm_tag_{name}")
            yield Input(placeholder="Custom tags (comma-separated)...", id="rm_tags_custom")

            with Horizontal(id="rm_form_buttons"):
                yield Button("Save Recipe", variant="primary", id="rm_save_btn")
                yield Button("Clear Form", id="rm_clear_btn")
            yield Label("", id="rm_save_status")

    def on_mount(self):
        self.query_one("#rm_url", Input).focus()
        self._update_tag_display()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "rm_scrape_btn":
            self._scrape()
        elif pid == "rm_save_btn":
            self._save()
        elif pid == "rm_clear_btn":
            self._clear_form()
        elif pid and pid.startswith("rm_tag_"):
            tag = pid[len("rm_tag_"):]
            if tag in self._selected_tags:
                self._selected_tags.discard(tag)
            else:
                self._selected_tags.add(tag)
            self._update_tag_display()

    def _update_tag_display(self):
        for name in ALL_TAGS:
            btn = self.query_one(f"#rm_tag_{name}", Button)
            btn.variant = "primary" if name in self._selected_tags else "default"
        if self._selected_tags:
            self.query_one("#rm_tags_display", Label).update(
                f"[dim]Selected:[/] {', '.join(sorted(self._selected_tags))}"
            )
        else:
            self.query_one("#rm_tags_display", Label).update("")

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "rm_url":
            self._scrape()

    def _scrape(self):
        url = self.query_one("#rm_url", Input).value.strip()
        status = self.query_one("#rm_scrape_status", Label)
        if not url:
            status.update("[bold red]Enter a URL[/]")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
            self.query_one("#rm_url", Input).value = url

        status.update("[dim]Scraping...[/]")
        try:
            scraper = scrape_me(url)
        except NoSchemaFoundInWildMode:
            status.update("[bold red]Unsupported site — try pasting manually[/]")
            return
        except Exception:
            try:
                scraper = scrape_me(url)
            except Exception as e:
                status.update(f"[bold red]Could not scrape: {e}[/]")
                return

        try:
            title = scraper.title()
            ingredients = "\n".join(scraper.ingredients())
            instructions = scraper.instructions()
            total_time = f"{scraper.total_time()} min"
            servings = scraper.yields()
        except Exception as e:
            status.update(f"[bold red]Error parsing: {e}[/]")
            return

        self.query_one("#rm_title_input", Input).value = title
        self.query_one("#rm_ingredients", TextArea).text = ingredients
        self.query_one("#rm_instructions", TextArea).text = instructions
        self.query_one("#rm_time", Input).value = str(total_time)
        self.query_one("#rm_servings", Input).value = str(servings)

        status.update(f"[bold green]Scraped:[/] {title}")

    def _save(self):
        title = self.query_one("#rm_title_input", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        ingredients = self.query_one("#rm_ingredients", TextArea).text
        instructions = self.query_one("#rm_instructions", TextArea).text
        custom = self.query_one("#rm_tags_custom", Input).value.strip()
        custom_tags = [t.strip() for t in custom.split(",") if t.strip()] if custom else []
        all_tags = sorted(self._selected_tags) + custom_tags

        if not all_tags:
            self.notify("Please select at least one tag.", severity="error")
            return

        tags = ", ".join(all_tags)
        total_time = self.query_one("#rm_time", Input).value.strip()
        servings = self.query_one("#rm_servings", Input).value.strip()
        source = self.query_one("#rm_url", Input).value.strip()

        path = save_recipe(title, ingredients, instructions,
                          tags=tags, total_time=total_time,
                          servings=servings, source=source)

        self.query_one("#rm_save_status", Label).update(
            f"[bold green]Saved:[/] [dim]{path}[/]"
        )

    def _clear_form(self):
        self.query_one("#rm_url", Input).value = ""
        self.query_one("#rm_title_input", Input).value = ""
        self.query_one("#rm_ingredients", TextArea).text = ""
        self.query_one("#rm_instructions", TextArea).text = ""
        self._selected_tags.clear()
        self._update_tag_display()
        self.query_one("#rm_tags_custom", Input).value = ""
        self.query_one("#rm_time", Input).value = ""
        self.query_one("#rm_servings", Input).value = ""
        self.query_one("#rm_scrape_status", Label).update("")
        self.query_one("#rm_save_status", Label).update("")
        self.query_one("#rm_url", Input).focus()
