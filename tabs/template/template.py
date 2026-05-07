from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder, TabPane, Label
from textual.containers import Container, Horizontal, VerticalScroll
import os

class TemplateTab(TabPane):
        
    DEFAULT_CSS = open(os.path.join(os.path.dirname(__file__), "template.tcss")).read()

    def compose(self) -> ComposeResult:
            
        yield VerticalScroll(
            
        Container(
                        
            Placeholder("This is a custom label for p1.", id="template_p1"),
                            
            Placeholder("Placeholder p2 here!", id="template_p2"),
                            
            Placeholder(id="template_p3"),
                            
            Placeholder(id="template_p4"),
                            
            Placeholder(id="template_p5"),
                            
            Placeholder(),
                            
            Horizontal(
                            
                Placeholder(variant="size", id="template_col1"),
                                    
                Placeholder(variant="text", id="template_col2"),
                                    
                Placeholder(variant="size", id="template_col3"),
                            
            id="template_c1",),
                            
        id="template_bot",),
                    
        Container(
                        
            Placeholder(variant="text", id="template_left"),
                            
            Placeholder(variant="size", id="template_topright"),
                            
            Placeholder(variant="text", id="template_botright"),
                        
        id="template_top",),
                    
    id="template_content",)
            

