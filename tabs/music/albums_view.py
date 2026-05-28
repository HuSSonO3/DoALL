from textual.app import ComposeResult
from textual.widgets import DataTable, Label
from textual.widget import Widget
from textual.containers import Vertical


class AlbumsView(Widget):
    """Displays albums as a DataTable with drill-down to tracks."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._albums = []
        self._tracks_view = None
        self._playback = None

    def compose(self) -> ComposeResult:
        with Vertical(id="music_albums_container"):
            yield Label("All Albums", id="music_albums_heading")
            yield DataTable(id="music_albums_table")

    def on_mount(self):
        table = self.query_one("#music_albums_table", DataTable)
        table.add_columns("Album", "Artist", "Tracks")
        table.cursor_type = "row"

    def set_albums(self, albums, tracks_view, playback):
        self._albums = albums
        self._tracks_view = tracks_view
        self._playback = playback
        self._refresh_table()

    def _refresh_table(self):
        table = self.query_one("#music_albums_table", DataTable)
        table.clear()
        for i, album in enumerate(self._albums):
            table.add_row(
                album["album"],
                album["artist"],
                str(album["track_count"]),
                key=str(i)
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id != "music_albums_table":
            return
        if not self._albums or not self._tracks_view:
            return

        row_key = event.row_key.value
        if row_key is None:
            return

        try:
            idx = int(row_key)
        except (ValueError, TypeError):
            return

        if idx < 0 or idx >= len(self._albums):
            return

        album = self._albums[idx]

        # Hide the entire AlbumsView widget, show TracksView with album detail
        self.display = False
        self._tracks_view.display = True
        self._tracks_view.show_album_tracks(album, self._playback)
