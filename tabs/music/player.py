import subprocess
import os
import signal
import shutil
from textual.message import Message


def detect_player():
    """Detect available system audio player. Returns player command or None."""
    for cmd in ["ffplay", "mpv", "aplay", "afplay"]:
        if shutil.which(cmd):
            return cmd
    return None


class TrackChanged(Message):
    """Posted when the current track changes."""
    def __init__(self, track, index):
        self.track = track
        self.index = index
        super().__init__()


class PlaybackStateChanged(Message):
    """Posted when playback state changes (playing/paused/stopped)."""
    def __init__(self, state):
        self.state = state
        super().__init__()


class TrackEnded(Message):
    """Posted when the current track finishes playing."""
    pass


class QueueChanged(Message):
    """Posted when the queue is modified (add/remove/reorder/clear)."""


class TrackProgress(Message):
    """Posted periodically with current playback position in seconds."""
    def __init__(self, elapsed, total):
        self.elapsed = elapsed
        self.total = total
        super().__init__()


class PlaybackEngine:
    """Manages audio playback via subprocess with ffplay/mpv/aplay.

    States: idle -> playing -> paused/stopped -> idle
    """

    def __init__(self, widget):
        self.widget = widget
        self._process = None
        self._state = "idle"
        self._queue = []
        self._current_index = -1
        self._elapsed = 0.0
        self._progress_timer = None
        self._player_cmd = detect_player()

        self._repeat_mode = "off"   # off, one, all
        self._shuffle = False
        self._shuffle_order = []

    @property
    def state(self):
        return self._state

    @property
    def current_track(self):
        if 0 <= self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None

    @property
    def queue(self):
        return list(self._queue)

    @property
    def current_index(self):
        return self._current_index

    @property
    def repeat_mode(self):
        return self._repeat_mode

    @property
    def shuffle(self):
        return self._shuffle

    def set_queue(self, tracks, start_index=0):
        self.stop()
        self._queue = list(tracks)
        self._current_index = start_index
        self._shuffle_order = list(range(len(self._queue)))
        if self._shuffle:
            import random
            random.shuffle(self._shuffle_order)
        self._notify_queue_changed()

    def _notify_queue_changed(self):
        self.widget.post_message(QueueChanged())

    def get_effective_index(self):
        if self._shuffle and self._shuffle_order:
            if self._current_index < len(self._shuffle_order):
                return self._shuffle_order[self._current_index]
        return self._current_index

    def add_to_queue(self, track):
        self._queue.append(track)
        if self._shuffle:
            import random
            idx = len(self._queue) - 1
            self._shuffle_order.insert(random.randint(0, len(self._shuffle_order)), idx)
        self._notify_queue_changed()

    def add_album_to_queue(self, tracks):
        for t in tracks:
            self._queue.append(t)
        if self._shuffle:
            import random
            new_indices = list(range(len(self._queue) - len(tracks), len(self._queue)))
            for idx in new_indices:
                self._shuffle_order.insert(random.randint(0, len(self._shuffle_order)), idx)
        self._notify_queue_changed()

    def remove_from_queue(self, index):
        if 0 <= index < len(self._queue):
            removed = self._queue.pop(index)
            if self._shuffle:
                self._shuffle_order = [i - 1 if i > index else i for i in self._shuffle_order if i != index]
            if index == self._current_index:
                was_playing = self._state == "playing"
                self._kill_process()
                if index >= len(self._queue):
                    self._current_index = len(self._queue) - 1
                if self._current_index < 0:
                    self._state = "idle"
                    self.widget.post_message(PlaybackStateChanged("idle"))
                elif was_playing:
                    self._play_current()
            elif index < self._current_index:
                self._current_index -= 1
            self._notify_queue_changed()
            return removed
        return None

    def move_in_queue(self, from_index, to_index):
        if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
            track = self._queue.pop(from_index)
            self._queue.insert(to_index, track)

            had_current = from_index == self._current_index
            if had_current:
                self._current_index = to_index
            else:
                if from_index < self._current_index and to_index >= self._current_index:
                    self._current_index -= 1
                elif from_index > self._current_index and to_index <= self._current_index:
                    self._current_index += 1
            self._notify_queue_changed()

    def clear_queue(self):
        self.stop()
        self._queue = []
        self._current_index = -1
        self._shuffle_order = []
        self._notify_queue_changed()

    def toggle_repeat(self):
        modes = ["off", "all", "one"]
        idx = modes.index(self._repeat_mode)
        self._repeat_mode = modes[(idx + 1) % len(modes)]
        return self._repeat_mode

    def toggle_shuffle(self):
        self._shuffle = not self._shuffle
        if self._shuffle:
            import random
            self._shuffle_order = list(range(len(self._queue)))
            random.shuffle(self._shuffle_order)
        return self._shuffle

    def play(self, index=None):
        if index is not None:
            if 0 <= index < len(self._queue):
                self._kill_process()
                self._current_index = index
            else:
                return

        if self._state == "paused" and self._current_index >= 0:
            self._resume_process()
            return

        if self._state == "playing" and index is None:
            return

        if not self._queue:
            return

        if self._current_index < 0:
            self._current_index = 0

        self._play_current()

    def pause(self):
        if self._state == "playing" and self._process:
            try:
                self._process.send_signal(signal.SIGSTOP)
                self._state = "paused"
                self._stop_progress_timer()
                self.widget.post_message(PlaybackStateChanged("paused"))
            except ProcessLookupError:
                pass

    def stop(self):
        self._kill_process()
        self._state = "idle"
        self._elapsed = 0.0
        self._stop_progress_timer()
        self.widget.post_message(PlaybackStateChanged("idle"))

    def next(self):
        if not self._queue:
            return
        self._kill_process()
        if self._repeat_mode == "one":
            self._play_current()
            return
        self._current_index += 1
        if self._current_index >= len(self._queue):
            if self._repeat_mode == "all":
                self._current_index = 0
            else:
                self._current_index = len(self._queue) - 1
                self._state = "idle"
                self.widget.post_message(PlaybackStateChanged("idle"))
                self.widget.post_message(TrackEnded())
                return
        self._play_current()

    def previous(self):
        if not self._queue:
            return
        self._kill_process()
        if self._elapsed > 3:
            self._play_current()
            return
        self._current_index -= 1
        if self._current_index < 0:
            self._current_index = len(self._queue) - 1
        self._play_current()

    def seek(self, seconds):
        if self._state == "playing" and self._queue and self._current_index >= 0:
            self._kill_process()
            self._elapsed = max(0, seconds)
            self._start_process(seek=self._elapsed)

    def cleanup(self):
        self._kill_process()
        self._stop_progress_timer()

    def _play_current(self):
        if self._current_index < 0 or self._current_index >= len(self._queue):
            return
        self._elapsed = 0.0

        # Probe actual duration if missing or zero
        track = self._queue[self._current_index]
        if track.get("duration", 0) <= 0:
            real = self._probe_duration(track["file_path"])
            if real > 0:
                track["duration"] = real

        self._start_process(seek=0)
        self._state = "playing"

        effective_idx = self.get_effective_index()
        if 0 <= effective_idx < len(self._queue):
            track = self._queue[effective_idx]
        else:
            track = self._queue[self._current_index]

        self.widget.post_message(TrackChanged(track, self._current_index))
        self.widget.post_message(PlaybackStateChanged("playing"))

    @staticmethod
    def _probe_duration(file_path):
        """Get actual duration in seconds via ffprobe. Returns 0 on failure."""
        if not shutil.which("ffprobe"):
            return 0
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", file_path],
                capture_output=True, text=True, timeout=10,
            )
            return float(result.stdout.strip())
        except Exception:
            return 0

    def _start_process(self, seek=0):
        track = self.current_track
        if not track:
            return

        file_path = track["file_path"]
        if not self._player_cmd:
            self.widget.post_message(PlaybackStateChanged("idle"))
            return

        try:
            if self._player_cmd == "ffplay":
                cmd = [
                    "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                ]
                if seek > 0:
                    cmd += ["-ss", str(seek)]
                cmd.append(file_path)
            elif self._player_cmd == "mpv":
                cmd = ["mpv", "--no-video", "--quiet"]
                if seek > 0:
                    cmd += [f"--start={seek}"]
                cmd.append(file_path)
            elif self._player_cmd == "aplay":
                cmd = ["aplay", file_path]
            elif self._player_cmd == "afplay":
                cmd = ["afplay", file_path]
            else:
                return

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._start_progress_timer()
            self._watch_process()
        except Exception:
            self._state = "idle"
            self.widget.post_message(PlaybackStateChanged("idle"))

    def _resume_process(self):
        if self._process and self._state == "paused":
            try:
                self._process.send_signal(signal.SIGCONT)
                self._state = "playing"
                self._start_progress_timer()
                self.widget.post_message(PlaybackStateChanged("playing"))
            except ProcessLookupError:
                self._state = "idle"
                self.widget.post_message(PlaybackStateChanged("idle"))

    def _kill_process(self):
        self._stop_progress_timer()
        if self._process:
            try:
                self._process.send_signal(signal.SIGCONT)
            except Exception:
                pass
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()
            except ProcessLookupError:
                pass
            self._process = None

    def _start_progress_timer(self):
        self._stop_progress_timer()
        try:
            self._progress_timer = self.widget.set_interval(0.5, self._tick_progress)
        except Exception:
            pass

    def _stop_progress_timer(self):
        if self._progress_timer:
            try:
                self._progress_timer.stop()
            except Exception:
                pass
            self._progress_timer = None

    def _tick_progress(self):
        if self._state == "playing":
            self._elapsed += 0.5
            track = self.current_track
            total = track.get("duration", 0) if track else 0
            if total <= 0:
                total = 0  # unknown — bar stays at 0; won't skip
            elif self._elapsed >= total:
                # Clamp at total; only the subprocess exit triggers next()
                self._elapsed = total
                self._stop_progress_timer()
            display_total = max(total, 1)
            display_elapsed = min(self._elapsed, display_total)
            self.widget.post_message(TrackProgress(display_elapsed, display_total))

    def _on_track_finished(self):
        self._stop_progress_timer()
        if self._repeat_mode == "one":
            self._play_current()
        else:
            self.next()

    def _watch_process(self):
        self.widget.run_worker(self._monitor_process(), exclusive=False)

    async def _monitor_process(self):
        import asyncio
        proc = self._process
        if proc:
            try:
                await asyncio.get_event_loop().run_in_executor(None, proc.wait)
            except Exception:
                pass
            if self._process == proc and self._state == "playing":
                self._stop_progress_timer()
                self.widget.post_message(TrackEnded())
                self._on_track_finished()
