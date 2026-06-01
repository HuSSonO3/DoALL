from textual.app import ComposeResult
from textual.widgets import TabPane, TabbedContent
from .slider_picker import SliderPicker


class ColorPickerTab(TabPane):

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("HSL", id="cp_tab_hsl"):
                yield SliderPicker(mode="hsl")
            with TabPane("RGB", id="cp_tab_rgb"):
                yield SliderPicker(mode="rgb")
