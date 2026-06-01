from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, RadioSet, RadioButton
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.binding import Binding

from .albums_view import AlbumsView
from .tracks_view import TracksView
from .playback_controls import PlaybackControls
from .queue_panel import QueuePanel
from .playlists import PlaylistsView
from .library import scan_directory
from .player import PlaybackEngine, TrackChanged, PlaybackStateChanged, TrackEnded, TrackProgress, QueueChanged


class MusicTab(TabPane):

    BINDINGS = [
        Binding("space", "play_pause", "Play/Pause"),
        Binding("n", "next_track", "Next Track"),
        Binding("p", "prev_track", "Previous Track"),
        Binding("s", "stop", "Stop"),
    ]

    def compose(self) -> ComposeResult:
        self._tracks = []
        self._albums = []
        self._playback = PlaybackEngine(self)

        with Horizontal(id="music_main_layout"):
            with VerticalScroll(id="music_library_panel"):
                yield Label("Music Library", id="music_library_title")
                with Horizontal(id="music_path_row"):
                    yield Input(placeholder="Enter music directory path...", id="music_path_input")
                    yield Button("Scan", id="music_scan_button")
                yield Label("", id="music_status_label")
                with RadioSet(id="music_view_toggle"):
                    yield RadioButton("Albums", id="music_view_albums", value=True)
                    yield RadioButton("Tracks", id="music_view_tracks")
                yield AlbumsView(id="music_albums_view")
                yield TracksView(id="music_tracks_view")

            with VerticalScroll(id="music_right_panel"):
                yield PlaybackControls(self._playback, id="music_playback_controls")
                yield QueuePanel(self._playback, id="music_queue_panel")
                yield PlaylistsView(self._playback, id="music_playlists_view")

        self._tracks_view = None
        self._albums_view_widget = None

    def on_mount(self):
        from .db import init_db, get_setting
        init_db()

        self._tracks_view = self.query_one("#music_tracks_view", TracksView)
        self._albums_view_widget = self.query_one("#music_albums_view", AlbumsView)
        self._playback_controls = self.query_one("#music_playback_controls", PlaybackControls)
        self._queue_panel = self.query_one("#music_queue_panel", QueuePanel)

        self._tracks_view.display = False

        # Restore saved library path and auto-scan
        saved = get_setting("library_path")
        if saved:
            self.query_one("#music_path_input", Input).value = saved
            self._scan_library()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "music_scan_button":
            self._scan_library()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "music_path_input":
            self._scan_library()

    def on_radio_set_changed(self, event: RadioSet.Changed):
        if event.pressed.id == "music_view_albums":
            self._albums_view_widget.display = True
            self._tracks_view.display = False
        elif event.pressed.id == "music_view_tracks":
            self._tracks_view.reset_to_all_tracks()
            self._albums_view_widget.display = False
            self._tracks_view.display = True

    def _scan_library(self):
        path = self.query_one("#music_path_input", Input).value.strip()
        if not path:
            self.query_one("#music_status_label", Label).update("[bold red]Please enter a path.[/]")
            return

        status = self.query_one("#music_status_label", Label)
        status.update("[bold yellow]Scanning...[/]")

        result = scan_directory(path)

        self._tracks = result["tracks"]
        self._albums = result["albums"]

        if result["errors"]:
            status.update(f"[bold red]{result['errors'][0]}[/]")
        else:
            from .db import save_setting
            save_setting("library_path", path)
            msg = f"Found {len(self._tracks)} tracks in {len(self._albums)} albums."
            if result["skipped_count"]:
                msg += f" Skipped {result['skipped_count']} files."
            status.update(msg)

        self._tracks_view.set_tracks(self._tracks, self._playback)
        self._albums_view_widget.set_albums(self._albums, self._tracks_view, self._playback)

    def action_play_pause(self):
        player = self._playback
        if player.state == "playing":
            player.pause()
        elif player.state == "paused":
            player.play()
        elif player.current_track:
            player.play()

    def action_next_track(self):
        self._playback.next()

    def action_prev_track(self):
        self._playback.previous()

    def action_stop(self):
        self._playback.stop()

    def on_unmount(self):
        self._playback.cleanup()

    def on_track_changed(self, message: TrackChanged):
        track = message.track
        self._playback_controls.show_track(track)
        self._queue_panel.sync_queue()

    def on_playback_state_changed(self, message: PlaybackStateChanged):
        self._playback_controls.show_state(message.state)
        self._queue_panel.sync_queue()

    def on_track_ended(self, message: TrackEnded):
        self._playback_controls.show_state("idle")

    def on_track_progress(self, message: TrackProgress):
        self._playback_controls.show_progress(message.elapsed, message.total)

    def on_queue_changed(self, message: QueueChanged):
        self._queue_panel.sync_queue()
