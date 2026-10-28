"""Face-down tic-tac-toe: a class game for the projector.

Nine photos from the current class lie face down on a 3x3 board, labelled
like Battleship -- rows A to C down the side, columns 1 to 3 across the top --
so a team can call "B2" across the room. The two teams, X and O, take turns
calling a square. It turns over, and the teacher names the person:

    right  -> the square is an O
    wrong  -> the square is an X

So the O team is betting on the teacher's memory and the X team against it.
Three in a row wins for that team; a full board with no line is a tie. Each
team may give one hint a game -- true, but not a giveaway, spoken in the room
-- and the board only keeps track of who has used theirs.

Face down because a team picking a face would be picking "the classmate we
think he doesn't know"; picking a square, nobody knows whose face is under it.

Built for a laptop on a projector with no touch screen: the person at the
laptop clicks what the teams call. The keys do the same -- Right, Wrong, and
F11 for full screen -- for anyone who would rather not aim a trackpad.

Every square turned over is logged like a quiz answer (mode "tictactoe"), so
class games show up in Your progress and in how often faces come up. No time
is logged: turning a square over to clicking Right includes talking, and would
skew the typical time the quiz measures from the first keystroke.
"""

import random
import tkinter as tk
import tkinter.font as tkfont

import theme

O_COLOUR = "#3987e5"     # categorical slot 1: the O team
X_COLOUR = "#d95926"     # categorical slot 2: the X team; teams are identities,
                         # not results, so they do not wear the status colours
ROWS, COLS = "ABC", "123"
LINES = ([[(r, c) for c in range(3)] for r in range(3)]
         + [[(r, c) for r in range(3)] for c in range(3)]
         + [[(i, i) for i in range(3)], [(i, 2 - i) for i in range(3)]])


class TicTacToe(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root, bg=theme.BG)
        self.app = app
        self.title("Face-down tic-tac-toe")
        self.k = self.winfo_fpixels("1p") / (96 / 72)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{int(sw * 0.8)}x{int(sh * 0.85)}+{int(sw * 0.1)}+{int(sh * 0.05)}")
        self.full = False

        self.status = theme.label(self, "", size=theme.SIZE_TITLE + 6, weight="bold")
        self.status.pack(pady=(int(16 * self.k), int(4 * self.k)))
        self.detail = theme.label(self, "", size=theme.SIZE_LABEL, fg=theme.MUTED)
        self.detail.pack()

        self.canvas = tk.Canvas(self, bg=theme.BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=int(20 * self.k))
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", self.click)

        bar = tk.Frame(self, bg=theme.BG)
        bar.pack(fill=tk.X, padx=int(24 * self.k), pady=int(16 * self.k))
        self.right_btn = theme.button(bar, "Right  →  O", lambda: self.answer(True),
                                      primary=True)
        self.wrong_btn = theme.button(bar, "Wrong  →  X", lambda: self.answer(False))
        self.hint_btn = {team: theme.button(bar, f"{team} team gave a hint",
                                            lambda t=team: self.use_hint(t))
                         for team in "OX"}
        self.right_btn.pack(side=tk.LEFT, padx=6)
        self.wrong_btn.pack(side=tk.LEFT, padx=6)
        self.hint_btn["O"].pack(side=tk.LEFT, padx=(30, 6))
        self.hint_btn["X"].pack(side=tk.LEFT, padx=6)
        theme.button(bar, "New game", self.new_game).pack(side=tk.RIGHT, padx=6)
        theme.button(bar, "Full screen (F11)", self.toggle_full).pack(side=tk.RIGHT, padx=6)

        for key in ("r", "R"):
            self.bind(key, lambda e: self.answer(True))
        for key in ("w", "W"):
            self.bind(key, lambda e: self.answer(False))
        self.bind("<F11>", lambda e: self.toggle_full())
        self.bind("<Escape>", lambda e: self.toggle_full() if self.full else None)
        self.new_game()
        self.focus_set()

    # -- the game ------------------------------------------------------------
    def new_game(self):
        people = list(self.app.students)
        if len(people) < 9:
            self.board = None
            self.status.config(text="Nine photos needed", fg=theme.TEXT)
            self.detail.config(text=f"This class has {len(people)}. "
                               "Choose a bigger class from File > Class.")
            self.draw()
            return
        faces = random.sample(people, 9)
        self.board = [[{"face": faces[r * 3 + c], "mark": None} for c in range(3)]
                      for r in range(3)]
        self.open = None            # (row, col) turned over, awaiting Right or Wrong
        self.hints = {"O": False, "X": False}
        self.hint_now = None        # the team that gave a hint on this square
        self.winner = None
        self.turn_team = random.choice("OX")
        self.round_no = None
        self.turn = 0
        self.refresh()

    def click(self, event):
        if not self.board or self.winner or self.open:
            return
        cell = self.cell_at(event.x, event.y)
        if cell and self.board[cell[0]][cell[1]]["mark"] is None:
            self.open = cell
            self.hint_now = None
            self.refresh()

    def use_hint(self, team):
        if not self.open or self.hints[team]:
            return
        self.hints[team] = True
        self.hint_now = team
        self.refresh()

    def answer(self, right):
        if not self.open:
            return
        r, c = self.open
        square = self.board[r][c]
        square["mark"] = "O" if right else "X"
        self.log(square["face"], right)
        self.open = None
        self.winner = self.find_winner()
        self.turn_team = "X" if self.turn_team == "O" else "O"
        self.refresh()

    def find_winner(self):
        for line in LINES:
            marks = {self.board[r][c]["mark"] for r, c in line}
            if len(marks) == 1 and None not in marks:
                return marks.pop(), line
        if all(sq["mark"] for row in self.board for sq in row):
            return "tie", None
        return None

    def log(self, face, right):
        """File the answer in the quiz log, so class games count like practice."""
        if self.round_no is None:
            self.round_no = theme.last_round() + 1
        self.turn += 1
        theme.log_answer(
            key=face["key"], label=face["label"], round=self.round_no, turn=self.turn,
            of=9, result=("hint" if self.hint_now else "correct") if right else "miss",
            seconds=None, typed=None, mode="tictactoe", hint_by=self.hint_now)

    # -- drawing -------------------------------------------------------------------
    def toggle_full(self):
        self.full = not self.full
        self.attributes("-fullscreen", self.full)

    def geometry_of_board(self):
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        label = tkfont.Font(font=theme.font(theme.SIZE_TITLE + 8, "bold")).metrics("linespace")
        size = max(60, min((w - label * 2) / 3, (h - label * 1.5) / 3))
        x0 = (w - 3 * size) / 2 + label / 2
        y0 = (h - 3 * size) / 2 + label * 0.6
        return x0, y0, size, label

    def cell_at(self, x, y):
        x0, y0, size, _ = self.geometry_of_board()
        c, r = int((x - x0) // size), int((y - y0) // size)
        return (r, c) if 0 <= r < 3 and 0 <= c < 3 else None

    def refresh(self):
        if not self.board:
            return
        o = sum(sq["mark"] == "O" for row in self.board for sq in row)
        x = sum(sq["mark"] == "X" for row in self.board for sq in row)
        if self.winner:
            who, _ = self.winner
            text = "A tie" if who == "tie" else f"{who} team wins"
            colour = theme.TEXT if who == "tie" else (O_COLOUR if who == "O" else X_COLOUR)
            self.status.config(text=text, fg=colour)
            self.detail.config(text=f"{o} right, {x} missed.  New game to play again.")
        elif self.open:
            r, c = self.open
            self.status.config(text=f"{ROWS[r]}{COLS[c]}: who is this?", fg=theme.TEXT)
            self.detail.config(text="Say the name, then Right (R) or Wrong (W)."
                               + ("  A hint was given." if self.hint_now else ""))
        else:
            team = self.turn_team
            self.status.config(text=f"{team} team, call a square",
                               fg=O_COLOUR if team == "O" else X_COLOUR)
            self.detail.config(text="Right makes an O, wrong makes an X.  "
                               "Three in a row wins.")
        for team, btn in self.hint_btn.items():
            used = self.hints[team]
            btn.config(text=f"{team} team hint used" if used else f"{team} team gave a hint")
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.board:
            return
        x0, y0, size, label = self.geometry_of_board()
        big = theme.font(theme.SIZE_TITLE + 8, "bold")
        for i in range(3):
            c.create_text(x0 + size * (i + 0.5), y0 - label * 0.6, text=COLS[i],
                          font=big, fill=theme.MUTED)
            c.create_text(x0 - label * 0.8, y0 + size * (i + 0.5), text=ROWS[i],
                          font=big, fill=theme.MUTED)
        gap = max(4, size * 0.03)
        self.images = []
        win_cells = set(self.winner[1]) if self.winner and self.winner[1] else set()
        for r in range(3):
            for col in range(3):
                sq = self.board[r][col]
                x, y = x0 + col * size + gap / 2, y0 + r * size + gap / 2
                s = size - gap
                face_up = sq["mark"] or self.open == (r, col) or self.winner
                if face_up:
                    img = theme.photo(sq["face"]["path"], box=int(s))
                    self.images.append(img)
                    c.create_image(x, y, image=img, anchor="nw")
                else:
                    c.create_rectangle(x, y, x + s, y + s, fill=theme.SURFACE,
                                       outline=theme.BORDER)
                    c.create_text(x + s / 2, y + s / 2, text=f"{ROWS[r]}{COLS[col]}",
                                  font=theme.font(theme.SIZE_TITLE + 14, "bold"),
                                  fill=theme.MUTED)
                if sq["mark"]:
                    colour = O_COLOUR if sq["mark"] == "O" else X_COLOUR
                    # A veil over the photo so the mark reads from the back row.
                    c.create_rectangle(x, y, x + s, y + s, fill=theme.BG,
                                       stipple="gray50", outline="")
                    m = s * 0.2
                    if sq["mark"] == "O":
                        c.create_oval(x + m, y + m, x + s - m, y + s - m,
                                      outline=colour, width=max(6, s * 0.07))
                    else:
                        c.create_line(x + m, y + m, x + s - m, y + s - m,
                                      fill=colour, width=max(6, s * 0.07), capstyle="round")
                        c.create_line(x + s - m, y + m, x + m, y + s - m,
                                      fill=colour, width=max(6, s * 0.07), capstyle="round")
                    c.create_text(x + s / 2, y + s - 10, anchor="s", text=sq["face"]["name"],
                                  font=theme.font(theme.SIZE_LABEL, "bold"), fill=theme.TEXT)
                if (r, col) in win_cells:
                    c.create_rectangle(x, y, x + s, y + s, outline=theme.TEXT,
                                       width=max(4, s * 0.03))
                if self.open == (r, col):
                    c.create_rectangle(x, y, x + s, y + s, outline=theme.ACCENT,
                                       width=max(4, s * 0.03))
