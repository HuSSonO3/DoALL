import random

from textual.app import ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.message import Message


class _FieldWidget(Widget):
    """Tiny widget whose ``render()`` draws the Pong play-field each frame.

    Using a proper ``render()`` instead of ``Static.update()`` avoids the
    flicker / jitter that can happen with rapid string replacement.
    """

    def __init__(self, owner: "PongWidget", **kwargs) -> None:
        kwargs.setdefault("id", "pong_field")
        super().__init__(**kwargs)
        self.owner = owner

    def render(self) -> RenderResult:
        return self.owner._render_field()


class PongWidget(Widget, can_focus=True):
    """A Pong game rendered live in the terminal.

    Player (left paddle) uses **↑** / **↓**.  The AI controls the right paddle.
    """

    WIDTH = 50
    HEIGHT = 20

    AI_SPEED = 0.8      # max pixels/tick the AI paddle can move
    MULTIPLIER = 0.55    # starting vertical multiplier (slow serve)
    MULT_STEP = 0.05     # increase every 3 paddle hits
    MULT_MAX = 1.0       # cap — keeps dy ≤ 1 cell/tick, no jitter

    BINDINGS = [
        Binding("up", "paddle_up", "Up"),
        Binding("down", "paddle_down", "Down"),
        Binding("space", "toggle_pause", "Play/Pause"),
    ]

    class Scored(Message):
        """Posted when a point is scored."""
        def __init__(self, side: str) -> None:
            super().__init__()
            self.side = side

    def compose(self) -> ComposeResult:
        self._paddle_left = float(self.HEIGHT // 2 - 2)
        self._paddle_right = float(self.HEIGHT // 2 - 2)
        self._score_player = 0
        self._score_ai = 0
        self._running = False
        self._tick_timer = None
        self._reset_ball()          # random initial serve

        with Container(id="pong_wrapper"):
            with Horizontal(id="pong_header"):
                yield Label("Pong", id="pong_title")
                yield Label("↑/↓ to move", id="pong_help")
            with Horizontal(id="pong_score_row"):
                yield Label("You: 0", id="pong_score_player")
                yield Label("AI: 0", id="pong_score_ai")
            yield _FieldWidget(self)
            with Horizontal(id="pong_buttons"):
                yield Button("Start", id="pong_start")
                yield Button("Pause", id="pong_pause")
                yield Button("Reset", id="pong_reset")

    # ── rendering ──────────────────────────────────────────────────

    def _render_field(self) -> str:
        """Return a fixed-width string of the current game state."""
        h, w = self.HEIGHT, self.WIDTH
        grid = [[" "] * w for _ in range(h)]

        for x in range(w):
            grid[0][x] = "▀"
            grid[h - 1][x] = "▄"

        cx = w // 2
        for y in range(1, h - 1):
            grid[y][cx] = "┊" if y % 2 == 0 else " "

        for dy in range(3):
            ly = int(self._paddle_left) + dy
            ry = int(self._paddle_right) + dy
            if 0 <= ly < h:
                grid[ly][1] = "█"
            if 0 <= ry < h:
                grid[ry][w - 2] = "█"

        bx = int(self._ball_x)
        by = int(self._ball_y)
        if 0 <= by < h and 0 <= bx < w:
            grid[by][bx] = "●"

        return "\n".join("".join(row) for row in grid)

    # ── game loop ──────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._tick_timer = self.set_interval(1 / 20, self._tick)

    def _tick(self) -> None:
        if not self._running:
            return

        self._ball_x += self._dx
        self._ball_y += self._dy

        # ── paddle hits (BEFORE wall bounces) ────────────────────
        # Checks the *trajectory segment* the ball travelled this tick,
        # not just its final position — prevents Y-tunneling when dy
        # is large enough to skip past the paddle in one frame.

        # left paddle  — map hit position to angle, speed locked by _mult
        if self._dx < 0 and int(self._ball_x) == 2:
            if self._y_crosses_paddle(self._paddle_left):
                self._ball_x = 3.0
                self._dx = 1.0
                hit = max(-1.0, min(1.0, (self._ball_y - self._paddle_left - 1.0)))
                self._dy = self._snap_dy(hit * self._mult)
                self._on_paddle_hit()
        # right paddle
        elif self._dx > 0 and int(self._ball_x) == self.WIDTH - 3:
            if self._y_crosses_paddle(self._paddle_right):
                self._ball_x = float(self.WIDTH - 4)
                self._dx = -1.0
                hit = max(-1.0, min(1.0, (self._ball_y - self._paddle_right - 1.0)))
                self._dy = self._snap_dy(hit * self._mult)
                self._on_paddle_hit()

        # ── wall bounces (AFTER paddle hits) ─────────────────────
        # Paddle hit already adjusted dy; wall bounce has the final
        # say so the ball always ends up moving away from the wall.
        if self._ball_y <= 1:
            self._ball_y = 1
            self._dy = abs(self._dy)
        elif self._ball_y >= self.HEIGHT - 2:
            self._ball_y = self.HEIGHT - 2
            self._dy = -abs(self._dy)

        # ── scoring ──────────────────────────────────────────────
        if self._ball_x <= 0:
            self._score_ai += 1
            self._reset_ball()
            self._update_scores()
            self.post_message(self.Scored("ai"))
        elif self._ball_x >= self.WIDTH - 1:
            self._score_player += 1
            self._reset_ball()
            self._update_scores()
            self.post_message(self.Scored("player"))

        self._ai_move()
        self.query_one("#pong_field", _FieldWidget).refresh()

    def _y_crosses_paddle(self, paddle_top: float) -> bool:
        """True if the ball's Y *trajectory segment* this tick overlaps
        the 3-row paddle range.  Catches the case where ``dy`` is large
        enough to skip past the paddle in a single frame (Y-tunneling)."""
        prev_y = self._ball_y - self._dy
        curr_y = self._ball_y
        y_lo = min(prev_y, curr_y)
        y_hi = max(prev_y, curr_y)
        p_lo = int(paddle_top)
        p_hi = p_lo + 2
        return y_lo <= p_hi and y_hi >= p_lo

    def _on_paddle_hit(self) -> None:
        """Called after every paddle hit.  Every 3 hits the vertical speed
        nudges up by a tiny amount — dx stays locked at 1.0 so horizontal
        movement always steps exactly 1 cell/tick (no X-jitter)."""
        self._rally_hits += 1
        if self._rally_hits % 3 == 0:
            self._mult = min(self._mult + self.MULT_STEP, self.MULT_MAX)
        self._ai_offset = random.uniform(-1.5, 1.5)

    @staticmethod
    def _snap_dy(raw: float) -> float:
        """Snap *raw* to the nearest integer so the ball always steps 1:1 or
        1:0 cells per tick.  At dx = 1.0 any fractional dy creates a visible
        staircase on the character grid — integer dy eliminates that."""
        return round(raw)

    # ── AI ─────────────────────────────────────────────────────────

    @staticmethod
    def _fold_y(y: float, lo: float, hi: float) -> float:
        """Fold *y* into [lo, hi] simulating wall bounces in O(1)."""
        h = hi - lo
        norm = y - lo
        return lo + h - abs(norm % (2 * h) - h)

    def _ai_move(self) -> None:
        """Move the right paddle toward the ball's projected intercept."""
        if self._dx > 0:
            paddle_x = self.WIDTH - 3
            steps = (paddle_x - self._ball_x) / self._dx
            projected = self._ball_y + self._dy * steps
            target = self._fold_y(projected, 1.0, float(self.HEIGHT - 2))
            target += self._ai_offset         # intentional imprecision
        else:
            target = self.HEIGHT / 2.0

        centre = self._paddle_right + 1.0
        if centre < target - self.AI_SPEED:
            self._paddle_right += self.AI_SPEED
        elif centre > target + self.AI_SPEED:
            self._paddle_right -= self.AI_SPEED
        else:
            self._paddle_right += target - centre

        self._paddle_right = max(0.0, min(float(self.HEIGHT - 4), self._paddle_right))

    def _reset_ball(self) -> None:
        self._mult = self.MULTIPLIER
        self._rally_hits = 0
        self._ball_x = float(self.WIDTH // 2)
        self._ball_y = float(self.HEIGHT // 2)
        # random serve direction — sometimes toward player, sometimes AI
        self._dx = 1.0 * random.choice((-1, 1))
        # random launch angle, snapped to integer for smooth stepping
        self._dy = self._snap_dy(random.uniform(-1.0, 1.0) * self._mult)
        self._ai_offset = random.uniform(-1.5, 1.5)

    def _update_scores(self) -> None:
        self.query_one("#pong_score_player", Label).update(f"You: {self._score_player}")
        self.query_one("#pong_score_ai", Label).update(f"AI: {self._score_ai}")

    # ── controls ───────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pong_start":
            self._running = True
            self.focus()
        elif event.button.id == "pong_pause":
            self._running = False
        elif event.button.id == "pong_reset":
            self._full_reset()

    def _full_reset(self) -> None:
        self._running = False
        self._score_player = 0
        self._score_ai = 0
        self._paddle_left = float(self.HEIGHT // 2 - 2)
        self._reset_ball()
        self._update_scores()
        self.query_one("#pong_field", _FieldWidget).refresh()

    def action_paddle_up(self) -> None:
        if self._running:
            self._paddle_left = max(0.0, self._paddle_left - 1)

    def action_paddle_down(self) -> None:
        if self._running:
            self._paddle_left = min(float(self.HEIGHT - 4), self._paddle_left + 1)

    def action_toggle_pause(self) -> None:
        self._running = not self._running
        if self._running:
            self.focus()
