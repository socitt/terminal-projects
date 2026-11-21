"""Chess: terminal entrypoint for narrow screens, iOS on-screen keyboard
(single key + Enter, no arrow/modifier chords). Squares are entered as
two single-key prompts each (file letter, then rank digit) — algebraic
notation split the same way go splits column/row, so every prompt
stays single-key+Enter compatible via `shared.input.prompt_choice`.

The game opens by asking for an opponent: a second human on the same
screen, or Nemo (nemo/) at one of three levels. Nemo plays Black.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nemo import ui as nemo_ui
from shared import input as input_module
from shared import term

import nemo_adapter
from board import (
    BLACK,
    SIZE,
    WHITE,
    apply_move,
    game_status,
    new_game,
    winner,
)

FILES = "abcdefgh"
RANKS = [str(d) for d in range(1, SIZE + 1)]
PROMOTION_KEYS = ["q", "r", "b", "n"]
NEMO_COLOR = BLACK


def render(state):
    board = state["board"]
    lines = []
    for row in range(SIZE - 1, -1, -1):
        cells = " ".join(board[row][col] or "." for col in range(SIZE))
        lines.append(f"{row + 1} {cells}")
    lines.append("  " + " ".join(FILES))
    return "\n".join(lines)


def _color_name(color):
    return "White" if color == WHITE else "Black"


def _square_name(square):
    row, col = square
    return f"{FILES[col]}{row + 1}"


def _prompt_square(label):
    file_key = input_module.prompt_choice(f"{label} file (a-h): ", list(FILES))
    rank_key = input_module.prompt_choice(f"{label} rank (1-8): ", RANKS)
    return int(rank_key) - 1, FILES.index(file_key)


def main():
    level = nemo_ui.prompt_opponent()
    rng = nemo_ui.make_rng()
    state = new_game()
    notes = []

    while True:
        term.clear_screen()
        print(render(state))
        for line in notes:
            print(line)
        notes = []

        status = game_status(state)
        if status == "checkmate":
            print(f"\nCheckmate! {_color_name(winner(state))} wins!")
            break
        if status == "stalemate":
            print("\nStalemate! Draw.")
            break

        if level is not nemo_ui.HUMAN and state["turn"] == NEMO_COLOR:
            (from_sq, to_sq, promotion), notes = nemo_ui.take_turn(
                nemo_adapter, state, level, rng)
            state = apply_move(state, from_sq, to_sq, promotion)
            notes = notes + [
                f"Nemo played {_square_name(from_sq)}-{_square_name(to_sq)}"]
            continue

        turn_name = _color_name(state["turn"])
        print(f"\n{turn_name}'s turn" + (" (in check)" if status == "check" else ""))

        from_sq = _prompt_square("From")
        to_sq = _prompt_square("To")

        piece = state["board"][from_sq[0]][from_sq[1]]
        promotion = None
        if piece and piece.upper() == "P" and to_sq[0] in (0, SIZE - 1):
            promo_key = input_module.prompt_choice(
                "Promote to (q/r/b/n): ", PROMOTION_KEYS
            )
            promotion = promo_key.upper()

        try:
            state = apply_move(state, from_sq, to_sq, promotion)
        except ValueError as exc:
            print(f"\nIllegal move: {exc}")
            input_module.get_key("Press Enter to continue... ")


if __name__ == "__main__":
    main()
