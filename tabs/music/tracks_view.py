from textual.app import ComposeResult
from textual.widgets import DataTable, Button
from textual.widget import Widget
from textual.containers import Horizontal, Vertical


class TracksView(Widget):
    """Displays a sortable DataTable of tracks — all tracks or a single album."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tracks = []
        self._album_mode = False
        self._album_tracks = []
        self._playback = None

    def compose(self) -> ComposeResult:
        with Vertical(id="music_tracks_container"):
            with Horizontal(id="music_tracks_header"):
                yield Button("Back to Albums", id="music_back_to_albums")
            with Horizontal(id="music_tracks_actions"):
                yield Button("Play Selected", id="music_track_play")
                yield Button("Add to Queue", id="music_track_add_queue")
                yield Button("Add Album to Queue", id="music_album_add_queue")
            yield DataTable(id="music_tracks_table")

    def on_mount(self):
        table = self.query_one("#music_tracks_table", DataTable)
        table.add_columns("Title", "Artist", "Album", "Duration")
        table.cursor_type = "row"
        self.query_one("#music_back_to_albums", Button).display = False

    def set_tracks(self, tracks, playback=None):
        self._tracks = tracks
        self._album_mode = False
        if playback is not None:
            self._playback = playback
        self._refresh_table(tracks)

    def show_album_tracks(self, album, playback):
        self._album_mode = True
        self._album_tracks = album["tracks"]
        self._playback = playback
        self._refresh_table(album["tracks"])
        self.query_one("#music_back_to_albums", Button).display = True

    def reset_to_all_tracks(self):
        self._album_mode = False
        self._album_tracks = []
        self._refresh_table(self._tracks)
        self.query_one("#music_back_to_albums", Button).display = False

    def _refresh_table(self, tracks):
        table = self.query_one("#music_tracks_table", DataTable)
        table.clear()
        for i, track in enumerate(tracks):
            dur = track.get("duration", 0)
            dur_str = f"{int(dur // 60)}:{int(dur % 60):02d}" if dur > 0 else "--:--"
            table.add_row(
                track["title"],
                track["artist"],
                track["album"],
                dur_str,
                key=str(i)
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id != "music_tracks_table":
            return

        tracks = self._album_tracks if self._album_mode else self._tracks
        row_key = event.row_key.value
        if row_key is None:
            return

        try:
            idx = int(row_key)
        except (ValueError, TypeError):
            return

        if idx < 0 or idx >= len(tracks):
            return

        if self._playback:
            self._playback.set_queue([tracks[idx]], 0)
            self._playback.play()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "music_back_to_albums":
            self._go_back_to_albums()
            return

        if not self._playback:
            return

        table = self.query_one("#music_tracks_table", DataTable)
        tracks = self._album_tracks if self._album_mode else self._tracks

        if event.button.id == "music_track_play":
            if table.row_count > 0:
                try:
                    row_key = table.ordered_rows[table.cursor_row].key.value
                    idx = int(row_key)
                    self._playback.set_queue([tracks[idx]], 0)
                    self._playback.play()
                except (IndexError, ValueError):
                    pass

        elif event.button.id == "music_track_add_queue":
            if table.row_count > 0:
                try:
                    row_key = table.ordered_rows[table.cursor_row].key.value
                    idx = int(row_key)
                    self._playback.add_to_queue(tracks[idx])
                    self.notify(f"Added: {tracks[idx]['title']}")
                except (IndexError, ValueError):
                    pass

        elif event.button.id == "music_album_add_queue":
            self._playback.add_album_to_queue(tracks)
            self.notify(f"Added {len(tracks)} tracks to queue")

    def _go_back_to_albums(self):
        self.display = False
        self.query_one("#music_back_to_albums", Button).display = False
        # Walk up the DOM to find MusicTab and show its albums view
        node = self.parent
        while node is not None:
            if hasattr(node, '_albums_view_widget'):
                node._albums_view_widget.display = True
                break
            node = node.parent
