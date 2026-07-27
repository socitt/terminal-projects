"""Tic-tac-toe: terminal entrypoint for narrow screens, iOS on-screen
keyboard (single key + Enter, no arrow/modifier chords).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared import input as input_module
from shared import term

from board import apply_move, is_draw, new_board, winner

CELL_KEYS = "123456789"


def render(board):
    rows = []
    for r in range(3):
        cells = [board[r * 3 + c] or str(r * 3 + c + 1) for c in range(3)]
        rows.append(" " + " | ".join(cells))
    return f"\n{term.hr(width=11, char='-')}\n".join(rows)


def main():
    board = new_board()
    turn = "X"
    while True:
        term.clear_screen()
        print(render(board))
        print(f"\n{turn}'s turn (1-9, blank cell)")
        key = input_module.prompt_choice("> ", CELL_KEYS)
        try:
            board = apply_move(board, int(key) - 1, turn)
        except ValueError:
            continue

        result = winner(board)
        if result:
            term.clear_screen()
            print(render(board))
            print(f"\n{result} wins!")
            return
        if is_draw(board):
            term.clear_screen()
            print(render(board))
            print("\nDraw!")
            return
        turn = "O" if turn == "X" else "X"


if __name__ == "__main__":
    main()
