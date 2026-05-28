from textual.app import ComposeResult
from textual.widgets import DataTable, Button, Label, Input
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen

from .db import (
    get_all_playlists, create_playlist, delete_playlist,
    get_playlist_tracks, add_track_to_playlist, clear_playlist_tracks, init_db
)


class PlaylistNameModal(ModalScreen):
    def compose(self) -> ComposeResult:
        with Container(id="music_modal_container"):
            yield Label("[bold]Playlist Name[/]", id="music_modal_text")
            yield Input(placeholder="Enter playlist name...", id="music_playlist_name_input")
            with Horizontal(id="music_modal_buttons"):
                yield Button("Save", id="music_modal_confirm")
                yield Button("Cancel", id="music_modal_cancel")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "music_modal_confirm":
            name = self.query_one("#music_playlist_name_input", Input).value.strip()
            self.dismiss(name if name else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted):
        name = event.value.strip()
        self.dismiss(name if name else None)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


class ConfirmDeleteModal(ModalScreen):
    def __init__(self, playlist_name):
        super().__init__()
        self._playlist_name = playlist_name

    def compose(self) -> ComposeResult:
        with Container(id="music_modal_container"):
            yield Label(f"[bold]Delete '{self._playlist_name}'?[/]", id="music_modal_text")
            with Horizontal(id="music_modal_buttons"):
                yield Button("Delete", id="music_modal_confirm", variant="error")
                yield Button("Cancel", id="music_modal_cancel")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "music_modal_confirm")

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


class PlaylistsView(Widget):

    def __init__(self, playback, **kwargs):
        super().__init__(**kwargs)
        self._playback = playback

    def compose(self) -> ComposeResult:
        with Vertical(id="music_playlists_container"):
            yield Label("Playlists", id="music_playlists_heading")
            yield DataTable(id="music_playlists_table")
            with Horizontal(id="music_playlists_buttons"):
                yield Button("Save Queue As...", id="music_playlist_save")
                yield Button("Load", id="music_playlist_load")
                yield Button("Delete", id="music_playlist_delete")

    def on_mount(self):
        init_db()
        table = self.query_one("#music_playlists_table", DataTable)
        table.add_columns("Name", "Tracks")
        table.cursor_type = "row"
        self._refresh_playlists()

    def _refresh_playlists(self):
        table = self.query_one("#music_playlists_table", DataTable)
        table.clear()
        playlists = get_all_playlists()
        for pl in playlists:
            table.add_row(pl["name"], str(pl["track_count"]), key=str(pl["id"]))

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id

        if pid == "music_playlist_save":
            if not self._playback.queue:
                self.notify("Queue is empty. Nothing to save.", severity="warning")
                return
            self.app.push_screen(PlaylistNameModal(), self._on_save_name)

        elif pid == "music_playlist_load":
            table = self.query_one("#music_playlists_table", DataTable)
            if table.row_count == 0:
                return
            try:
                row_key = table.ordered_rows[table.cursor_row].key.value
                pl_id = int(row_key)
                tracks = get_playlist_tracks(pl_id)
                queue_tracks = [{
                    "file_path": t["file_path"],
                    "title": t["title"],
                    "artist": t["artist"],
                    "album": t["album"],
                    "duration": t["duration"],
                } for t in tracks]
                self._playback.set_queue(queue_tracks, 0)
                self.notify(f"Loaded {len(queue_tracks)} tracks")
            except (IndexError, ValueError):
                pass

        elif pid == "music_playlist_delete":
            table = self.query_one("#music_playlists_table", DataTable)
            if table.row_count == 0:
                return
            try:
                row_key = table.ordered_rows[table.cursor_row].key.value
                pl_id = int(row_key)
                rows = get_all_playlists()
                pl_name = next((r["name"] for r in rows if r["id"] == pl_id), "Unknown")
                self.app.push_screen(ConfirmDeleteModal(pl_name), lambda confirmed: self._on_delete(confirmed, pl_id))
            except (IndexError, ValueError):
                pass

    def _on_save_name(self, name):
        if not name:
            return
        pl_id = create_playlist(name)
        if pl_id is None:
            self.notify(f"Playlist '{name}' already exists.", severity="error")
            return
        clear_playlist_tracks(pl_id)
        for i, track in enumerate(self._playback.queue):
            add_track_to_playlist(pl_id, track, i)
        self._refresh_playlists()
        self.notify(f"Playlist '{name}' saved with {len(self._playback.queue)} tracks.")

    def _on_delete(self, confirmed, pl_id):
        if confirmed:
            delete_playlist(pl_id)
            self._refresh_playlists()
            self.notify("Playlist deleted.")
