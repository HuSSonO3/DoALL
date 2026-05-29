from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.containers import Grid, Container, Horizontal
from ._win_modal import WinModal


class TicTacToeWidget(Widget):
    """A 3x3 Tic Tac Toe game for two players sharing the keyboard."""

    def compose(self) -> ComposeResult:
        self._board = [""] * 9
        self._current = "X"
        self._scores = {"X": 0, "O": 0, "draw": 0}

        with Container(id="ttt_wrapper"):
            yield Label("Tic Tac Toe", id="ttt_title")
            yield Label("X's turn", id="ttt_status")
            with Grid(id="ttt_grid"):
                for i in range(9):
                    yield Button("", id=f"ttt_cell_{i}", classes="ttt_cell")
            with Horizontal(id="ttt_scores"):
                yield Label("X: 0", id="ttt_score_x")
                yield Label("Draw: 0", id="ttt_score_draw")
                yield Label("O: 0", id="ttt_score_o")
            yield Button("New Game", id="ttt_reset")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ttt_reset":
            self._reset_board()
            return

        if not event.button.id or not event.button.id.startswith("ttt_cell_"):
            return

        idx = int(event.button.id.split("_")[-1])
        if self._board[idx] != "":
            return  # cell already taken

        # Place the mark
        self._board[idx] = self._current
        event.button.label = self._current
        event.button.variant = "primary" if self._current == "X" else "error"

        winner = self._check_winner()
        if winner:
            self._scores[winner] += 1
            self._update_scores()
            self._disable_cells()
            self.app.push_screen(
                WinModal(f"[bold]{winner} wins![/]"),
                self._on_win_modal_done,
            )
        elif "" not in self._board:
            self._scores["draw"] += 1
            self._update_scores()
            self.app.push_screen(
                WinModal("It's a draw!"),
                self._on_win_modal_done,
            )
        else:
            self._current = "O" if self._current == "X" else "X"
            self.query_one("#ttt_status", Label).update(f"{self._current}'s turn")

    def _check_winner(self) -> str | None:
        b = self._board
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6),              # diagonals
        ]
        for a, bb, c in wins:
            if b[a] and b[a] == b[bb] == b[c]:
                return b[a]
        return None

    def _reset_board(self) -> None:
        self._board = [""] * 9
        self._current = "X"
        for i in range(9):
            btn = self.query_one(f"#ttt_cell_{i}", Button)
            btn.label = ""
            btn.variant = "default"
            btn.disabled = False
        self.query_one("#ttt_status", Label).update("X's turn")

    def _disable_cells(self) -> None:
        for i in range(9):
            self.query_one(f"#ttt_cell_{i}", Button).disabled = True

    def _on_win_modal_done(self, new_game: bool) -> None:
        if new_game:
            self._reset_board()

    def _update_scores(self) -> None:
        self.query_one("#ttt_score_x", Label).update(f"X: {self._scores['X']}")
        self.query_one("#ttt_score_o", Label).update(f"O: {self._scores['O']}")
        self.query_one("#ttt_score_draw", Label).update(f"Draw: {self._scores['draw']}")
