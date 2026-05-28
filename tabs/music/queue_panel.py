from textual.app import ComposeResult
from textual.widgets import DataTable, Button, Label
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.screen import ModalScreen




class ClearQueueModal(ModalScreen):
    def compose(self) -> ComposeResult:
        with Container(id="music_modal_container"):
            yield Label("[bold]Clear the entire queue?[/]", id="music_modal_text")
            with Horizontal(id="music_modal_buttons"):
                yield Button("Yes, Clear", id="music_modal_confirm", variant="error")
                yield Button("Cancel", id="music_modal_cancel")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "music_modal_confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


class QueuePanel(Widget):

    BINDINGS = [
        Binding("ctrl+up", "move_up", "Move Up"),
        Binding("ctrl+down", "move_down", "Move Down"),
    ]

    def __init__(self, playback, **kwargs):
        super().__init__(**kwargs)
        self._playback = playback

    def compose(self) -> ComposeResult:
        with Vertical(id="music_queue_container"):
            yield Label("Queue", id="music_queue_heading")
            yield DataTable(id="music_queue_table")
            with Horizontal(id="music_queue_buttons"):
                yield Button("Clear All", id="music_queue_clear")
                yield Button("Remove", id="music_queue_remove")

    def on_mount(self):
        table = self.query_one("#music_queue_table", DataTable)
        table.add_columns("#", "Title", "Artist")
        table.cursor_type = "row"

    def sync_queue(self):
        self._refresh_queue()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id != "music_queue_table":
            return
        row_key = event.row_key.value
        if row_key is None:
            return
        try:
            idx = int(row_key)
        except (ValueError, TypeError):
            return
        self._playback.play(index=idx)

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        p = self._playback

        if pid == "music_queue_clear":
            self.app.push_screen(ClearQueueModal(), self._on_clear_confirmed)
        elif pid == "music_queue_remove":
            table = self.query_one("#music_queue_table", DataTable)
            if table.row_count > 0:
                try:
                    idx = int(table.ordered_rows[table.cursor_row].key.value)
                    p.remove_from_queue(idx)
                    self._refresh_queue()
                except (IndexError, ValueError):
                    pass

    def _on_clear_confirmed(self, confirmed):
        if confirmed:
            self._playback.clear_queue()
            self._refresh_queue()

    # def _move_current(self, delta):
    #     table = self.query_one("#music_queue_table", DataTable)
    #     if table.row_count == 0:
    #         return
    #     try:
    #         idx = int(table.ordered_rows[table.cursor_row].key.value)
    #         new_idx = idx + delta
    #         if 0 <= new_idx < len(self._playback.queue):
    #             self._playback.move_in_queue(idx, new_idx)
    #             self._refresh_queue()
    #             table.cursor_row = new_idx
    #     except (IndexError, ValueError):
    #         pass

    def _refresh_queue(self):
        table = self.query_one("#music_queue_table", DataTable)
        table.clear()
        effective = self._playback.get_effective_index()
        for i, track in enumerate(self._playback.queue):
            prefix = "▶ " if i == effective and self._playback.state != "idle" else ""
            table.add_row(
                str(i + 1),
                f"{prefix}{track['title']}",
                track["artist"],
                key=str(i)
            )

