"""Go: terminal entrypoint for narrow screens, iOS on-screen keyboard
(single key + Enter, no arrow/modifier chords). Coordinates are
entered as two single-digit prompts (column, then row) rather than
one combined token, for the same reason.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared import input as input_module
from shared import term

from board import BLACK, SIZE, apply_move, opponent, new_board, score, winner

DIGIT_KEYS = [str(d) for d in range(1, SIZE + 1)]
COLUMN_KEYS = DIGIT_KEYS + ["p"]


def render(board):
    header = "  " + " ".join(DIGIT_KEYS)
    lines = [header]
    for row in range(SIZE):
        cells = " ".join(board[row][col] or "." for col in range(SIZE))
        lines.append(f"{row + 1} {cells}")
    return "\n".join(lines)


def main():
    board = new_board()
    previous_board = None
    turn = BLACK
    consecutive_passes = 0

    while consecutive_passes < 2:
        term.clear_screen()
        print(render(board))
        print(f"\n{turn}'s turn")
        col_key = input_module.prompt_choice("Column (1-9) or P to pass: ", COLUMN_KEYS)

        if col_key == "p":
            consecutive_passes += 1
            turn = opponent(turn)
            continue

        row_key = input_module.prompt_choice("Row (1-9): ", DIGIT_KEYS)
        col, row = int(col_key) - 1, int(row_key) - 1

        try:
            new_board_state = apply_move(board, row, col, turn, previous_board)
        except ValueError as exc:
            print(f"\nIllegal move: {exc}")
            input_module.get_key("Press Enter to continue... ")
            continue

        previous_board = board
        board = new_board_state
        turn = opponent(turn)
        consecutive_passes = 0

    term.clear_screen()
    print(render(board))
    black_score, white_score = score(board)
    print(f"\nBlack: {black_score}  White: {white_score}")
    result = winner(board)
    print(f"{result} wins!" if result else "Tie!")


if __name__ == "__main__":
    main()
