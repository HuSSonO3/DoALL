from textual.app import ComposeResult
from textual.widgets import Button, Label, ProgressBar
from textual.widget import Widget
from textual.containers import Horizontal, Vertical


class PlaybackControls(Widget):

    REPEAT_LABELS = {"off": "Repeat: Off", "all": "Repeat: All", "one": "Repeat: One"}

    def __init__(self, playback, **kwargs):
        super().__init__(**kwargs)
        self._playback = playback

    def compose(self) -> ComposeResult:
        with Vertical(id="music_playback_container"):
            yield Label("No track playing", id="music_now_playing")
            yield Label("", id="music_now_artist")
            with Horizontal(id="music_transport_row"):
                yield Button("⏮", id="music_prev_button")
                yield Button("▶", id="music_play_button")
                yield Button("⏹", id="music_stop_button")
                yield Button("⏭", id="music_next_button")
            with Horizontal(id="music_seek_row"):
                yield Label("0:00", id="music_time_elapsed")
                yield ProgressBar(total=100, show_eta=False, id="music_seek_bar")
                yield Label("0:00", id="music_time_total")
            with Horizontal(id="music_mode_row"):
                yield Button("Repeat: Off", id="music_repeat_button")
                yield Button("Shuffle: Off", id="music_shuffle_button")

    def on_mount(self):
        self._update_button_states()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        p = self._playback

        if pid == "music_play_button":
            if p.state == "playing":
                p.pause()
            else:
                p.play()
        elif pid == "music_stop_button":
            p.stop()
        elif pid == "music_next_button":
            p.next()
        elif pid == "music_prev_button":
            p.previous()
        elif pid == "music_repeat_button":
            mode = p.toggle_repeat()
            self.query_one("#music_repeat_button", Button).label = self.REPEAT_LABELS[mode]
            self._update_mode_styles()
        elif pid == "music_shuffle_button":
            active = p.toggle_shuffle()
            self.query_one("#music_shuffle_button", Button).label = f"Shuffle: {'On' if active else 'Off'}"
            self._update_mode_styles()
        self._update_button_states()

    def show_track(self, track):
        if track:
            self.query_one("#music_now_playing", Label).update(f"[bold]{track['title']}[/]")
            self.query_one("#music_now_artist", Label).update(f"{track['artist']} - {track['album']}")
        self._update_button_states()

    def show_state(self, state):
        if state == "idle":
            self.query_one("#music_now_playing", Label).update("No track playing")
            self.query_one("#music_now_artist", Label).update("")
        self._update_button_states()

    def show_progress(self, elapsed, total):
        bar = self.query_one("#music_seek_bar", ProgressBar)
        if total <= 0:
            # Unknown duration — fill the bar as elapsed grows, up to a
            # sliding window so it always shows some movement.
            window = max(elapsed + 1, 1)
            bar.update(total=window, progress=elapsed % window)
            total_str = "--:--"
        else:
            bar.update(total=total, progress=min(elapsed, total))
            total_str = f"{int(total // 60)}:{int(total % 60):02d}"
        self.query_one("#music_time_elapsed", Label).update(
            f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        )
        self.query_one("#music_time_total", Label).update(total_str)

    def _update_button_states(self):
        p = self._playback
        play_btn = self.query_one("#music_play_button", Button)

        if p.state == "playing":
            play_btn.label = "⏸"
        elif p.state == "paused":
            play_btn.label = "▶"
        else:
            play_btn.label = "▶"

        has_track = p.current_track is not None
        for bid in ["music_prev_button", "music_next_button", "music_stop_button"]:
            btn = self.query_one(f"#{bid}", Button)
            btn.disabled = not has_track

        self._update_mode_styles()

    def _update_mode_styles(self):
        p = self._playback
        repeat_btn = self.query_one("#music_repeat_button", Button)
        shuffle_btn = self.query_one("#music_shuffle_button", Button)

        repeat_btn.label = self.REPEAT_LABELS[p.repeat_mode]
        shuffle_btn.label = f"Shuffle: {'On' if p.shuffle else 'Off'}"

        if p.repeat_mode != "off":
            repeat_btn.add_class("mode-active")
        else:
            repeat_btn.remove_class("mode-active")

        if p.shuffle:
            shuffle_btn.add_class("mode-active")
        else:
            shuffle_btn.remove_class("mode-active")
