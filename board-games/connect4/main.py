"""Connect Four: terminal entrypoint for narrow screens, iOS on-screen
keyboard (single key + Enter, no arrow/modifier chords).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared import input as input_module
from shared import term

from board import COLS, apply_move, is_draw, new_board, valid_moves, winner

COLUMN_KEYS = "1234567"


def render(board):
    header = " ".join(str(c + 1) for c in range(COLS))
    rows = [" ".join(cell or "." for cell in row) for row in board]
    return header + "\n" + "\n".join(rows)


def main():
    board = new_board()
    turn = "X"
    while True:
        term.clear_screen()
        print(render(board))
        print(f"\n{turn}'s turn (1-{COLS}, column)")
        key = input_module.prompt_choice("> ", COLUMN_KEYS)
        col = int(key) - 1
        if col not in valid_moves(board):
            continue
        board = apply_move(board, col, turn)

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
