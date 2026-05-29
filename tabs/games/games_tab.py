from textual.app import ComposeResult
from textual.widgets import TabPane, TabbedContent
from .tictactoe import TicTacToeWidget
from .pong import PongWidget
from .snake import SnakeWidget
from .connect4 import ConnectFourWidget


class GamesTab(TabPane):
    """Games module – pick a game from the inner tabs."""

    def compose(self) -> ComposeResult:
        with TabbedContent(id="games_tabbed"):
            with TabPane("Tic Tac Toe", id="tictactoe"):
                yield TicTacToeWidget()
            with TabPane("Pong", id="pong"):
                yield PongWidget()
            with TabPane("Snake", id="snake"):
                yield SnakeWidget()
            with TabPane("Connect 4", id="connect4"):
                yield ConnectFourWidget()
