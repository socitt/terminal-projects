"""Tic-tac-toe: terminal entrypoint for narrow screens, iOS on-screen
keyboard (single key + Enter, no arrow/modifier chords).

The game opens by asking for an opponent: a second human on the same
screen, or Nemo (nemo/) at one of three levels. Nemo plays O.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nemo import ui as nemo_ui
from shared import input as input_module
from shared import term

import nemo_adapter
from board import apply_move, is_draw, new_board, winner

NEMO_MARK = "O"

CELL_KEYS = "123456789"


def render(board):
    rows = []
    for r in range(3):
        cells = [board[r * 3 + c] or str(r * 3 + c + 1) for c in range(3)]
        rows.append(" " + " | ".join(cells))
    return f"\n{term.hr(width=11, char='-')}\n".join(rows)


def _show(board, notes):
    term.clear_screen()
    print(render(board))
    for line in notes:
        print(line)


def main():
    level = nemo_ui.prompt_opponent()
    rng = nemo_ui.make_rng()
    board = new_board()
    turn = "X"
    notes = []
    while True:
        _show(board, notes)
        notes = []
        if level is not nemo_ui.HUMAN and turn == NEMO_MARK:
            index, notes = nemo_ui.take_turn(
                nemo_adapter, (board, turn), level, rng)
            board = apply_move(board, index, turn)
            notes = notes + [f"Nemo played {index + 1}"]
        else:
            print(f"\n{turn}'s turn (1-9, blank cell)")
            key = input_module.prompt_choice("> ", CELL_KEYS)
            try:
                board = apply_move(board, int(key) - 1, turn)
            except ValueError:
                continue

        result = winner(board)
        if result:
            _show(board, notes)
            print(f"\n{result} wins!")
            return
        if is_draw(board):
            _show(board, notes)
            print("\nDraw!")
            return
        turn = "O" if turn == "X" else "X"


if __name__ == "__main__":
    main()
