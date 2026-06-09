"""Recipe Manager — main widget and tab wrapper."""

from textual.app import ComposeResult
from textual.widgets import TabPane, TabbedContent, Label
from textual.widget import Widget
from textual.containers import Vertical

from .add_tab import AddRecipeTab
from .browse_tab import BrowseRecipesTab


class RecipeManagerWidget(Widget):

    def compose(self) -> ComposeResult:
        with Vertical(id="rm_container"):
            yield Label("[bold]Recipe Manager[/]", id="rm_title")
            with TabbedContent(id="rm_tabs"):
                yield AddRecipeTab("Add Recipe", id="rm_add_tab")
                yield BrowseRecipesTab("My Recipes", id="rm_browse_tab")

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        if event.pane is not None and event.pane.id == "rm_browse_tab":
            self.call_after_refresh(
                lambda: self.query_one("#rm_browse_tab", BrowseRecipesTab)._refresh_list()
            )


class RecipesTab(TabPane):
    def compose(self) -> ComposeResult:
        yield RecipeManagerWidget()
