from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.containers import Grid, Container, Horizontal
from textual.binding import Binding
from ._win_modal import WinModal


class ConnectFourWidget(Widget, can_focus=True):
    """Two-player Connect Four — drop tokens into columns, get 4 in a row."""

    COLS = 7
    ROWS = 6

    BINDINGS = [
        Binding("1", "drop(0)", "Col 1"),
        Binding("2", "drop(1)", "Col 2"),
        Binding("3", "drop(2)", "Col 3"),
        Binding("4", "drop(3)", "Col 4"),
        Binding("5", "drop(4)", "Col 5"),
        Binding("6", "drop(5)", "Col 6"),
        Binding("7", "drop(6)", "Col 7"),
    ]

    def compose(self) -> ComposeResult:
        self._board = [[None] * self.COLS for _ in range(self.ROWS)]
        self._current = "●"   # Player 1 starts
        self._scores = {"●": 0, "○": 0, "draw": 0}
        self._game_over = False

        with Container(id="c4_wrapper"):
            yield Label("Connect Four", id="c4_title")
            yield Label("●'s turn", id="c4_status")

            # column drop buttons
            with Horizontal(id="c4_columns"):
                for col in range(self.COLS):
                    yield Button("↓", id=f"c4_drop_{col}", classes="c4_drop")

            # board grid  (ROWS × COLS)
            with Grid(id="c4_grid"):
                for row in range(self.ROWS):
                    for col in range(self.COLS):
                        yield Label("·", id=f"c4_cell_{row}_{col}", classes="c4_cell")

            with Horizontal(id="c4_scores"):
                yield Label("●: 0", id="c4_score_p1")
                yield Label("Draw: 0", id="c4_score_draw")
                yield Label("○: 0", id="c4_score_p2")

            yield Button("New Game", id="c4_reset")

    # ── column drop ────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "c4_reset":
            self._reset_board()
            return
        if event.button.id and event.button.id.startswith("c4_drop_"):
            self._try_drop(int(event.button.id.split("_")[-1]))

    def action_drop(self, col: int) -> None:
        self._try_drop(col)

    def _try_drop(self, col: int) -> None:
        """Drop the current player's token into *col* (0-indexed)."""
        if self._game_over:
            return

        row = self._drop_row(col)
        if row is None:
            return  # column full

        self._board[row][col] = self._current
        cell = self.query_one(f"#c4_cell_{row}_{col}", Label)
        cell.update(self._current)
        cell.set_class(row % 2 == 0, "c4_even")
        cell.set_class(row % 2 != 0, "c4_odd")
        if self._current == "●":
            cell.add_class("c4_p1")
            cell.remove_class("c4_p2")
        else:
            cell.add_class("c4_p2")
            cell.remove_class("c4_p1")

        if self._check_win(row, col):
            self._scores[self._current] += 1
            self._update_scores()
            self._game_over = True
            self.app.push_screen(
                WinModal(f"[bold]{self._current} wins![/]"),
                self._on_win_modal_done,
            )
            return

        if all(self._board[r][c] is not None
               for r in range(self.ROWS) for c in range(self.COLS)):
            self._scores["draw"] += 1
            self._update_scores()
            self._game_over = True
            self.app.push_screen(
                WinModal("It's a draw!"),
                self._on_win_modal_done,
            )
            return

        self._current = "○" if self._current == "●" else "●"
        self.query_one("#c4_status", Label).update(f"{self._current}'s turn")

    def _drop_row(self, col: int) -> int | None:
        """Return the lowest empty row index for *col*, or None if full."""
        for row in range(self.ROWS - 1, -1, -1):
            if self._board[row][col] is None:
                return row
        return None

    # ── win detection ──────────────────────────────────────────────

    def _check_win(self, row: int, col: int) -> bool:
        """Check 4 directions from (row, col) for a run of 4."""
        token = self._board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # → ↓ ↘ ↙
        for dr, dc in directions:
            count = 1
            # positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self._board[r][c] == token:
                count += 1
                r += dr
                c += dc
            # negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self._board[r][c] == token:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                return True
        return False

    # ── helpers ────────────────────────────────────────────────────

    def _on_win_modal_done(self, new_game: bool) -> None:
        if new_game:
            self._reset_board()

    def _reset_board(self) -> None:
        self._board = [[None] * self.COLS for _ in range(self.ROWS)]
        self._current = "●"
        self._game_over = False
        for row in range(self.ROWS):
            for col in range(self.COLS):
                cell = self.query_one(f"#c4_cell_{row}_{col}", Label)
                cell.update("·")
                cell.remove_class("c4_p1", "c4_p2")
        self.query_one("#c4_status", Label).update("●'s turn")

    def _update_scores(self) -> None:
        self.query_one("#c4_score_p1", Label).update(f"●: {self._scores['●']}")
        self.query_one("#c4_score_p2", Label).update(f"○: {self._scores['○']}")
        self.query_one("#c4_score_draw", Label).update(f"Draw: {self._scores['draw']}")
