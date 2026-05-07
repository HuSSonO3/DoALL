from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label, DirectoryTree, TextArea, Input
from textual.containers import Container, Horizontal, HorizontalScroll, VerticalScroll
import os
from pathlib import Path

class DashboardTab(TabPane):
        
    DEFAULT_CSS = open(os.path.join(os.path.dirname(__file__), "noting.tcss")).read()


    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """
    def compose(self) -> ComposeResult:
            
        yield Container(

                DirectoryTree("./file_holders/noting", id="noting_tree"),
                
                TextArea.code_editor(self.TEXT, language="markdown",id="noting_text")              
                ,id="noting_container",
                )

        yield Input(placeholder="filename.md", id="new_file_input")

            

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.log("HIIIIIIIIIIIIIIIIDasfskjfs")
        self.log(event.path)
        file = self.query_one(TextArea)
        file.load_text(event.path.read_text())
     

    def on_text_area_changed(self, event: TextArea.Changed):
        path = self.query_one(DirectoryTree)
        path = path.cursor_node.data.path
        path.write_text(event.text_area.text)        

    def on_input_submitted(self, event: Input.Submitted):
        filename = event.value.strip()
        filename = filename + ".md"
        if filename:
            new_file = Path("./file_holders/noting") / filename
            new_file.touch()
            self.query_one(DirectoryTree).reload()
            event.input.value = ""
        event.input.display = False 

    def on_key(self, event):
        if event.key == "n":
            input = self.query_one("#new_file_input")
            input.display = not input.display
            if input.display:
                input.focus()