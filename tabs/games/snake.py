import random
from collections import deque

from textual.app import ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.message import Message


class _SnakeField(Widget):
    """Renders the snake play-field via ``render()``."""

    def __init__(self, owner: "SnakeWidget", **kwargs) -> None:
        kwargs.setdefault("id", "snake_field")
        super().__init__(**kwargs)
        self.owner = owner

    def render(self) -> RenderResult:
        return self.owner._render_field()


class SnakeWidget(Widget, can_focus=True):
    """Snake — arrow keys to steer, eat ★ to grow and score."""

    GRID_W = 48
    GRID_H = 22

    BASE_FPS = 12         # horizontal: 12 moves/sec
    MAX_FPS = 18
    FPS_STEP = 0.01       # tiny speed bump every food eaten

    # Terminal characters are ~2× taller than wide, so a vertical step
    # covers twice the visual distance of a horizontal step.  We skip
    # every other tick while moving vertically to keep the visual speed
    # even in all directions.
    VERT_EVERY = 2        # vertical: 6 moves/sec at BASE_FPS

    BINDINGS = [
        Binding("up", "turn_up", "Up"),
        Binding("down", "turn_down", "Down"),
        Binding("left", "turn_left", "Left"),
        Binding("right", "turn_right", "Right"),
        Binding("space", "toggle_pause", "Play/Pause"),
        Binding("r", "restart", "Restart"),
    ]

    class GameOver(Message):
        """Posted when the snake crashes."""
        def __init__(self, score: int) -> None:
            super().__init__()
            self.score = score

    def compose(self) -> ComposeResult:
        self._init_state()

        with Container(id="snake_wrapper"):
            with Horizontal(id="snake_header"):
                yield Label("Snake", id="snake_title")
                yield Label("Arrows to steer", id="snake_help")
            yield Label("Score: 0", id="snake_score")
            yield _SnakeField(self)
            with Horizontal(id="snake_buttons"):
                yield Button("Start", id="snake_start")
                yield Button("Pause", id="snake_pause")
                yield Button("Reset", id="snake_reset")

    def _init_state(self) -> None:
        """Set / reset all game state."""
        cx, cy = self.GRID_W // 2, self.GRID_H // 2
        self._snake = deque([
            (cx, cy),
            (cx - 1, cy),
            (cx - 2, cy),
        ])
        self._dir = (1, 0)
        self._next_dir = (1, 0)
        self._food = self._spawn_food()
        self._score = 0
        self._running = False
        self._dead = False
        self._fps = self.BASE_FPS
        self._tick_timer = None
        self._vert_tick = 0

    # ── rendering ──────────────────────────────────────────────────

    def _render_field(self) -> str:
        h, w = self.GRID_H, self.GRID_W
        grid = [[" "] * w for _ in range(h)]

        for x in range(w):
            grid[0][x] = "▀"
            grid[h - 1][x] = "▄"
        for y in range(1, h - 1):
            grid[y][0] = "█"
            grid[y][w - 1] = "█"

        for i, (sx, sy) in enumerate(self._snake):
            if 0 <= sy < h and 0 <= sx < w:
                grid[sy][sx] = "●" if i == 0 else "○"

        fx, fy = self._food
        if 0 <= fy < h and 0 <= fx < w:
            grid[fy][fx] = "★"

        return "\n".join("".join(row) for row in grid)

    # ── game loop ──────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._start_timer()

    def _start_timer(self) -> None:
        if self._tick_timer:
            self._tick_timer.stop()
        self._tick_timer = self.set_interval(1 / self._fps, self._tick)

    def _tick(self) -> None:
        if not self._running:
            return

        # lock in queued direction (prevent 180° reverse)
        dx, dy = self._next_dir
        if (dx, dy) != (-self._dir[0], -self._dir[1]):
            self._dir = (dx, dy)

        # throttle vertical movement — terminal chars are ~2:1
        if self._dir[1] != 0:
            self._vert_tick += 1
            if self._vert_tick < self.VERT_EVERY:
                return  # skip this tick
        self._vert_tick = 0

        hx, hy = self._snake[0]
        dx, dy = self._dir
        nx, ny = hx + dx, hy + dy

        # wall
        if nx <= 0 or nx >= self.GRID_W - 1 or ny <= 0 or ny >= self.GRID_H - 1:
            self._game_over()
            return

        # self
        if (nx, ny) in self._snake:
            self._game_over()
            return

        self._snake.appendleft((nx, ny))

        if (nx, ny) == self._food:
            self._score += 1
            self._update_score()
            self._food = self._spawn_food()
            self._fps = min(self.MAX_FPS, self._fps + self.FPS_STEP)
            self._start_timer()
        else:
            self._snake.pop()

        self.query_one("#snake_field", _SnakeField).refresh()

    def _spawn_food(self) -> tuple[int, int]:
        empty = [
            (x, y)
            for y in range(1, self.GRID_H - 1)
            for x in range(1, self.GRID_W - 1)
            if (x, y) not in self._snake
        ]
        return random.choice(empty) if empty else (1, 1)

    def _game_over(self) -> None:
        self._running = False
        self._dead = True
        self.query_one("#snake_score", Label).update(
            f"[bold red]GAME OVER[/] — Score: {self._score}"
        )
        self.post_message(self.GameOver(self._score))

    def _update_score(self) -> None:
        self.query_one("#snake_score", Label).update(f"Score: {self._score}")

    # ── controls ───────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "snake_start":
            if self._dead:
                self._full_reset()
            else:
                self._running = True
            self.focus()
        elif event.button.id == "snake_pause":
            if not self._dead:
                self._running = False
        elif event.button.id == "snake_reset":
            self._full_reset()

    def _full_reset(self) -> None:
        self._running = False
        if self._tick_timer:                 # stop old timer FIRST —
            self._tick_timer.stop()          # otherwise _init_state drops
        self._init_state()                   # the reference & it leaks
        self._update_score()
        self._start_timer()
        self.query_one("#snake_field", _SnakeField).refresh()

    def action_turn_up(self) -> None:
        self._next_dir = (0, -1)

    def action_turn_down(self) -> None:
        self._next_dir = (0, 1)

    def action_turn_left(self) -> None:
        self._next_dir = (-1, 0)

    def action_turn_right(self) -> None:
        self._next_dir = (1, 0)

    def action_restart(self) -> None:
        self._full_reset()

    def action_toggle_pause(self) -> None:
        if self._dead:
            return
        self._running = not self._running
        if self._running:
            self.focus()
