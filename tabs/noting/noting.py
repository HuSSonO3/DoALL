from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Footer, Placeholder, TabPane, Label, DirectoryTree, TextArea, Input, Button, Markdown
from textual.containers import Container, Horizontal, HorizontalScroll, VerticalScroll, Grid
import os
from pathlib import Path
from textual.binding import Binding
import textwrap

class FileModal(ModalScreen):
    def compose(self) -> ComposeResult:
        with Container(id="new_file_container"):
            yield Label("[bold]File Name?[/bold]")
            yield Input(placeholder="filename")
            yield Label("Press Escape to close", id="small_label")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        filename = event.value.strip()
        if filename:
            if not filename.endswith(".md"):
                filename = filename + ".md"
            self.dismiss(filename)
        else:
            self.dismiss(None) 

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

class DeleteModal(ModalScreen):
    def compose(self) -> ComposeResult:
        with Container(id="delete_file_container"):
            yield Label("[bold]Are you sure you want to delete the file?[/bold]")
            yield Button("Delete File", variant="error")
            yield Label("Press Escape to close", id="small_label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        path = self.app.query_one("#noting_tree", DirectoryTree)
        path = path.cursor_node.data.path
        if path:
            if path.is_file():
                path.unlink(missing_ok=True)
                self.app.query_one("#noting_tree", DirectoryTree).reload()
                self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

class NoteTakingTab(TabPane):

    BINDINGS = [
        Binding("n", "new_file", "New File"),
        Binding("d", "delete_file", "Delete File"),
    ]

    TEXT = textwrap.dedent(
    """\
    ---
    Hello!! Welcome to note taker!
    \n The base format for files here is .md for stylization if wanted.

    # Markdown Cheat Sheet
    - Typography: 
        - *emphasis* use one pair of `*`. 
        - **strong** use two pair of `*`. 
        - `inline code` use one pair of `.
        - _italic_ use one pair of `_`.
        - ~~strikethrough~~ use two pairs of `~`.    
    - Headers: use `#` `##` or `###` before the text.
    - Lists: use `-` before the item, for nested lists:
        - go to the next line and press tab to add space then another `-`.
    1. Another option is to use numbers `1.`
    > Blockqoute uses one `>` before the text.
    > > You can do nested blockqoutes by adding one more `>` every time you nest.
    - [link text](https://example.com) [text] and directly next to it (link).
    - For code block use three of **`** then the name of the language then at the end of the code block add another three of **```**.
    ```python
        def hello():
           print("hello world")
    ```
    - Horizontal Rule by adding `---` in a new line.
    ---
    - Go to New line: add `\\` and `n` "without space between them"
    \n
    
    - Tables:\n
        - To make a table you need to seperate columns by `|` and close the row with `|` as well.
        - If you want to add length to the column add multiple `-`.\n

    | Name            | Type   | Default | Description                       |
    | --------------- | ------ | ------- | ----------------------------------|
    | show_test   | Test | Test  | Test |
    """
    )
    def compose(self) -> ComposeResult:
            
        yield Container(
            DirectoryTree("./file_holders/noting", id="noting_tree"),    
            Container(Markdown(self.TEXT, id="noting_view"), 
            TextArea.code_editor("", language="markdown", id="noting_text"),
            id="noting_scroll")   
        ,id="noting_container",)
            

    async def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.log("HIIIIIIIIIIIIIIIIDasfskjfs")
        self.log(event.path)

        # Check if there is a markdown widget and remove it.
        # markdown = self.query("#noting_view")
        # if markdown:
        #     await markdown.remove()

        # # Check if there isnt a Text area and add it.
        # if not self.query("#noting_text"):
        #     await self.query_one("#noting_scroll").mount(
        #         TextArea.code_editor("", language="markdown", id="noting_text")
        #     )
        #     self.query_one("#noting_text", TextArea).focus()

        self.query_one("#noting_text").display = True
        self.query_one("#noting_view").display = False

        file = self.query_one("#noting_text", TextArea)
        file.load_text(event.path.read_text())
    
    async def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected):
        self.log("VHASahauioshdaujuiahduiah")
        self.log(event.path)

        # Check if there isnt a Markdown and add it
        # if not self.query("#noting_view"):
        #     await self.query_one("#noting_scroll").mount(
        #         Markdown(self.TEXT, id="noting_view")
        #     )

        # # check if there is a Text area and remove it
        # text = self.query("#noting_text")
        # if text:
        #     await text.remove()

        self.query_one("#noting_text").display = False
        self.query_one("#noting_view").display = True
        self.query_one("#noting_view", Markdown).update(self.TEXT)

    def on_descendant_focus(self, event):
        if event.widget.id == "noting_tree":
            self._show_preview()
    

    def _show_preview(self) -> None:
        ta = self.query("#noting_text")
        if ta:
            content = ta.first(TextArea).text
            self.query_one("#noting_text").display = False
            self.query_one("#noting_view").display = True
            self.query_one("#noting_view", Markdown).update(content)

    def on_text_area_changed(self, event: TextArea.Changed):
        path = self.query_one(DirectoryTree)
        path = path.cursor_node.data.path
        path.write_text(event.text_area.text)        

    def on_key(self, event):
        if event.key == "n":
            self.app.push_screen(FileModal(), self.file_handler)

    def file_handler(self, filename: str | None):
        if filename:
            new_file = Path("./file_holders/noting") / filename
            new_file.touch()
            self.app.query_one("#noting_tree", DirectoryTree).reload()
    
    def action_delete_file(self):
        path = self.app.query_one("#noting_tree", DirectoryTree)
        path = path.cursor_node.data.path
        if str(path).endswith(".md"):
            self.app.push_screen(DeleteModal())

    # def action_paste_clipboard(self) -> None:
    #     try:
    #         # Linux
    #         content = subprocess.run(
    #             ["xclip", "-selection", "clipboard", "-o"],
    #             capture_output=True, text=True
    #         ).stdout
    #         # or xsel:
    #         # content = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True).stdout
            
    #         ta = self.query_one("#noting_text", TextArea)
    #         ta.insert(content)
    #     except Exception as e:
    #         self.notify(f"Clipboard error: {e}", severity="error")