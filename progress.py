"""Your progress: the quiz log, one page at a time, each with a caption.

A carousel of five pages, moved through with Previous and Next or the arrow
keys:
  1. at a glance: the headline numbers
  2. how each round went: correct / slow or hint / missed or skipped
  3. time to first keystroke, as a box plot per round
  4. the hardest faces right now, by the game's own index
  5. the names you mixed up
One thing per page, as large as the window allows, because four charts in one
window left each too squashed to read. Under each is a caption, like the label
beside a painting: how to read the page, then what your own numbers say. The
caption is written from the log each time it opens, never typed in.

Drawn on a Tk canvas rather than with a charting library, so it works in every
copy -- the Windows exe, a Mac with python.org Python, the drive -- with nothing
to install. Everything comes from quiz-log.jsonl through theme.load_log, the
reader the quiz uses, so the pages and the deal cannot disagree.

Fonts are in points and the display decides the pixels, so every length is
scaled by the display (`self.k`) and text is placed by its measured size.
"""

import collections
import statistics
import tkinter as tk
import tkinter.font as tkfont

import roster
import theme

# Status colours carry a result, never a series; each always has a text label.
GOOD = "#0ca30c"
WARN = "#fab219"
BAD = "#d03b3b"
BLUE = "#3987e5"          # the one hue for magnitude (times, index)
GRID = theme.BORDER
INK_ON_WARN = "#0b0b0b"

RESULTS = (("Correct", ("correct",), GOOD),
           ("Slow or hint", ("slow", "hint"), WARN),
           ("Missed or skipped", ("miss", "skip"), BAD))

MAX_ROUNDS = 15           # most recent rounds shown in the per-round charts
MAX_FACES = 12


def name_of(key):
    return roster.display_name(roster.parse(key + ".jpg"))


def clean_seconds(entries):
    return [e["seconds"] for e in entries
            if e.get("seconds") is not None and e["result"] in ("correct", "slow")]


def quartiles(values):
    values = sorted(values)
    if len(values) < 2:
        return values[0], values[0], values[0]
    q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q1, q2, q3


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


class ProgressWindow(tk.Toplevel):
    def __init__(self, app, copies):
        """`copies` is the quiz's own rule for how often a face comes up,
        passed in so the caption quotes the game rather than a second copy."""
        super().__init__(app.root, bg=theme.BG)
        self.app = app
        self.copies = copies
        self.label = app.klass or "All classes"
        self.title(f"Your progress — {self.label}")
        self.transient(app.root)

        self.k = self.winfo_fpixels("1p") / (96 / 72)   # 1 at 96 dpi
        self.W = int(900 * self.k)
        self.pad = int(32 * self.k)
        self.tip = None

        self.log = theme.load_log()
        self.mine = [e for e in self.log if not app.klass or e.get("label") == app.klass]
        self.rounds = collections.defaultdict(list)
        for e in self.mine:
            self.rounds[e["round"]].append(e)
        self.recent = sorted(self.rounds)[-MAX_ROUNDS:]

        height = min(int(860 * self.k), int(self.winfo_screenheight() * 0.85) - 80)
        self.canvas = tk.Canvas(self, width=self.W, height=height, bg=theme.BG,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        nav = tk.Frame(self, bg=theme.BG)
        nav.pack(fill=tk.X, padx=self.pad, pady=(0, int(20 * self.k)))
        theme.button(nav, "‹  Previous", lambda: self.turn(-1)).pack(side=tk.LEFT)
        theme.button(nav, "Next  ›", lambda: self.turn(1), primary=True).pack(side=tk.RIGHT)
        self.where = theme.label(nav, "", size=theme.SIZE_BODY, fg=theme.MUTED)
        self.where.pack(side=tk.LEFT, expand=True)

        if self.mine:
            self.pages = [
                ("At a glance", self.glance_caption, self.glance),
                ("How each round went", self.results_caption, self.results_chart),
                ("Time to first keystroke, by round", self.times_caption, self.times_chart),
                ("Hardest faces right now", self.faces_caption, self.faces_chart),
                ("Names you mixed up", self.mixups_caption, self.mixups),
            ]
        else:
            self.pages = [("Your progress", lambda: (
                "Nothing to show yet",
                "Every quiz answer is saved as you play, and this window draws "
                "them. Play a round of Quiz and come back."), lambda c, a, b: None)]
        self.page = 0
        self.bind("<Left>", lambda e: self.turn(-1))
        self.bind("<Right>", lambda e: self.turn(1))
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self.show)
        self.focus_set()

    # -- carousel ----------------------------------------------------------
    def turn(self, step):
        self.page = (self.page + step) % len(self.pages)
        self.show()

    def show(self):
        c = self.canvas
        c.delete("all")
        self.tip = None
        W, H = self.W, int(c.cget("height"))
        title, caption, draw = self.pages[self.page]
        sub = self.text(c, self.pad, int(20 * self.k), f"{self.label}",
                        theme.SIZE_SMALL, theme.MUTED)
        t = self.text(c, self.pad, self.bottom(c, sub) + int(2 * self.k), title,
                      theme.SIZE_TITLE + 2, weight="bold")
        top = self.bottom(c, t) + int(20 * self.k)
        cap_top = self.caption(c, *caption(), H)
        draw(c, top, cap_top - int(24 * self.k))
        self.where.config(text=f"{self.page + 1} of {len(self.pages)}"
                          if len(self.pages) > 1 else "")

    def caption(self, c, heading, body, H):
        """The museum label: drawn at the foot of the page, measured, so the
        chart above takes whatever height is left. Returns its top edge."""
        inset, bar = int(18 * self.k), int(4 * self.k)
        width = self.W - 2 * self.pad - 2 * inset - bar
        h_item = self.text(c, 0, 0, heading, theme.SIZE_BODY, weight="bold", width=width)
        b_item = self.text(c, 0, 0, body, theme.SIZE_BODY, theme.TEXT, width=width)
        hh = c.bbox(h_item)[3] - c.bbox(h_item)[1]
        bh = c.bbox(b_item)[3] - c.bbox(b_item)[1]
        gap = int(6 * self.k)
        box_h = inset * 2 + hh + gap + bh
        y0 = H - int(12 * self.k) - box_h
        x0 = self.pad
        c.create_rectangle(x0, y0, self.W - self.pad, y0 + box_h,
                           fill=theme.SURFACE, outline="")
        c.create_rectangle(x0, y0, x0 + bar, y0 + box_h, fill=BLUE, outline="")
        c.coords(h_item, x0 + bar + inset, y0 + inset)
        c.coords(b_item, x0 + bar + inset, y0 + inset + hh + gap)
        c.tag_raise(h_item)
        c.tag_raise(b_item)
        return y0

    # -- measuring and drawing -----------------------------------------------
    def measure(self, s, size=theme.SIZE_BODY, weight="normal"):
        return tkfont.Font(font=theme.font(size, weight)).measure(s)

    def line(self, size=theme.SIZE_BODY, weight="normal"):
        return tkfont.Font(font=theme.font(size, weight)).metrics("linespace")

    def text(self, c, x, y, s, size=theme.SIZE_BODY, fill=theme.TEXT, weight="normal",
             anchor="nw", **kw):
        return c.create_text(x, y, text=s, fill=fill, anchor=anchor,
                             font=theme.font(size, weight), **kw)

    def bottom(self, c, item):
        return c.bbox(item)[3]

    def legend(self, c, x, y, entries):
        sw = self.line() * 0.6
        bottom = y
        for text, colour in entries:
            t = self.text(c, x + sw + 8 * self.k, y, text, theme.SIZE_BODY, theme.MUTED)
            x0, y0, x1, y1 = c.bbox(t)
            mid = (y0 + y1) / 2
            c.create_rectangle(x, mid - sw / 2, x + sw, mid + sw / 2, fill=colour, outline="")
            x, bottom = x1 + 26 * self.k, max(bottom, y1)
        return bottom

    def hover(self, c, tag, message):
        """Show `message` beside the pointer while it is over anything tagged `tag`."""
        def leave(_event=None):
            if self.tip:
                for i in self.tip:
                    c.delete(i)
                self.tip = None

        def enter(event):
            leave()
            t = self.text(c, event.x + 16 * self.k, event.y + 12 * self.k, message,
                          theme.SIZE_SMALL)
            x0, y0, x1, y1 = c.bbox(t)
            c.move(t, min(0, self.W - self.pad / 2 - x1),
                   min(0, int(c.cget("height")) - 8 - y1))
            x0, y0, x1, y1 = c.bbox(t)
            m = 8 * self.k
            r = c.create_rectangle(x0 - m, y0 - m, x1 + m, y1 + m,
                                   fill=theme.SURFACE, outline=GRID)
            c.tag_raise(t, r)
            self.tip = (r, t)

        c.tag_bind(tag, "<Enter>", enter)
        c.tag_bind(tag, "<Leave>", leave)

    # -- 1. at a glance ------------------------------------------------------------
    def glance_numbers(self):
        days = sorted({e.get("at", "")[:10] for e in self.mine})
        times = clean_seconds(self.mine)
        best = theme.load_scores().get(self.app.section, {}).get("best", 0)
        return days, times, best

    def glance(self, c, top, bottom):
        days, times, best = self.glance_numbers()
        tiles = [("Answers", f"{len(self.mine)}"),
                 ("Rounds", f"{len(self.rounds)}"),
                 ("Days played", f"{len(days)}"),
                 ("Typical time", f"{statistics.median(times):.1f} s" if times else "–"),
                 ("Best streak", f"{best}"),
                 ("Faces seen", f"{len({e['key'] for e in self.mine})}")]
        cols, gap = 3, int(16 * self.k)
        rows = (len(tiles) + cols - 1) // cols
        w = (self.W - 2 * self.pad - gap * (cols - 1)) / cols
        h = min((bottom - top - gap * (rows - 1)) / rows, 170 * self.k)
        inset = int(20 * self.k)
        for i, (name, value) in enumerate(tiles):
            x = self.pad + (i % cols) * (w + gap)
            y = top + (i // cols) * (h + gap)
            c.create_rectangle(x, y, x + w, y + h, fill=theme.SURFACE, outline="")
            self.text(c, x + inset, y + inset, name, theme.SIZE_BODY, theme.MUTED)
            self.text(c, x + inset, y + h - inset, value, theme.SIZE_FEATURE + 14,
                      weight="bold", anchor="sw")

    def glance_caption(self):
        days, times, best = self.glance_numbers()
        span = (f"on {days[0]}" if len(days) == 1
                else f"over {len(days)} days, {days[0]} to {days[-1]}")
        body = (f"{plural(len(self.mine), 'answer')} in {plural(len(self.rounds), 'round')}, "
                f"{span}. An answer is any turn: right, wrong or skipped. Typical time is "
                f"the median time from the photo appearing to your first keystroke, counted "
                f"over correct answers only, so typing a long name does not slow it down. "
                f"Best streak is the most names in a row without a miss, kept per class.")
        return "Every turn you have taken, counted", body

    # -- 2. how each round went ------------------------------------------------------
    def counts(self, r):
        return [sum(e["result"] in kinds for e in self.rounds[r]) for _, kinds, _ in RESULTS]

    def results_chart(self, c, top, bottom):
        y = self.legend(c, self.pad, top, [(n, col) for n, _, col in RESULTS])
        y += int(16 * self.k)
        rounds = self.recent
        left = self.pad + max(self.measure(f"Round {r}") for r in rounds) + int(14 * self.k)
        right = self.W - self.pad - self.measure("000") - int(12 * self.k)
        scale = (right - left) / max(len(self.rounds[r]) for r in rounds)
        row = min((bottom - y) / len(rounds), 3.0 * self.line())
        bar = row * 0.7
        for r in rounds:
            es, counts = self.rounds[r], self.counts(r)
            mid = y + row / 2
            self.text(c, left - 14 * self.k, mid, f"Round {r}", fill=theme.MUTED, anchor="e")
            x, tag = left, f"round{r}"
            for (_, _, colour), n in zip(RESULTS, counts):
                if not n:
                    continue
                w = n * scale
                c.create_rectangle(x, mid - bar / 2, x + w - 2, mid + bar / 2,
                                   fill=colour, outline="", tags=tag)
                if w > self.measure(str(n)) + 12 * self.k and bar > self.line() * 0.8:
                    self.text(c, x + (w - 2) / 2, mid, str(n),
                              fill=INK_ON_WARN if colour == WARN else "#ffffff",
                              weight="bold", anchor="center", tags=tag)
                x += w
            self.text(c, x + 10 * self.k, mid, str(len(es)), fill=theme.MUTED, anchor="w")
            self.hover(c, tag, f"Round {r}, {es[0].get('at', '')[:10]}\n"
                       + "\n".join(f"{n}: {k}" for (n, _, _), k in zip(RESULTS, counts))
                       + f"\n{len(es)} turns")
            y += row

    def results_caption(self):
        first, last = self.recent[0], self.recent[-1]
        good, warn, bad = self.counts(last)
        said = (f"Your latest round, round {last}, had {plural(len(self.rounds[last]), 'turn')}: "
                f"{good} correct, {warn} slow or with a hint, {bad} missed or skipped.")
        if first != last:
            said = (f"Round {first} had {plural(len(self.rounds[first]), 'turn')}. " + said)
        body = ("Each bar is one quiz round, and its length is how many turns it had. "
                "Green is a quick, clean answer. Amber is right but slow (more than 1.5 "
                "times your typical time) or after a hint. Red is a miss or a skip. A miss "
                "ends the round, so red usually sits at the end. Rounds get shorter as the "
                "game learns which faces you know, because those come up once instead of "
                "two or three times. " + said)
        return "One bar for each round", body

    # -- 3. time to first keystroke --------------------------------------------------
    def time_stats(self):
        stats = {}
        for r in self.recent:
            t = clean_seconds(self.rounds[r])
            if t:
                stats[r] = (sorted(t), quartiles(t))
        return stats

    def times_chart(self, c, top, bottom):
        stats = self.time_stats()
        if not stats:
            return
        # Whiskers reach 1.5 box-lengths; anything past is a dot. The scale stops
        # above the highest whisker so one long pause cannot flatten every box;
        # dots beyond it sit on the top edge.
        whiskers = {}
        for r, (t, (q1, _, q3)) in stats.items():
            reach = 1.5 * (q3 - q1)
            inside = [v for v in t if q1 - reach <= v <= q3 + reach]
            whiskers[r] = (min(inside), max(inside))
        hi_all = max(hi for _, hi in whiskers.values())
        top_v = max(1.0, hi_all * 1.25, min(max(max(t) for t, _ in stats.values()), hi_all * 2))
        y0 = top + self.line(theme.SIZE_SMALL) // 2
        base = bottom - self.line() - int(10 * self.k)
        h = base - y0
        left = self.pad + self.measure("10 s", theme.SIZE_SMALL) + int(14 * self.k)
        right = self.W - self.pad

        def sy(v):
            return base - min(v, top_v) / top_v * h

        step = 0.5 if top_v <= 3 else 1 if top_v <= 8 else 2
        v = 0.0
        while v <= top_v + 1e-9:
            c.create_line(left, sy(v), right, sy(v), fill=GRID)
            self.text(c, left - 10 * self.k, sy(v), f"{v:g} s", theme.SIZE_SMALL,
                      theme.MUTED, anchor="e")
            v += step
        slot = (right - left) / len(stats)
        bw = min(90 * self.k, slot * 0.45)
        dot = 5 * self.k
        for i, (r, (t, (q1, q2, q3))) in enumerate(sorted(stats.items())):
            cx = left + slot * (i + 0.5)
            lo, hi = whiskers[r]
            tag = f"box{r}"
            c.create_line(cx, sy(lo), cx, sy(q1), fill=BLUE, width=2, tags=tag)
            c.create_line(cx, sy(q3), cx, sy(hi), fill=BLUE, width=2, tags=tag)
            for end in (lo, hi):
                c.create_line(cx - bw / 4, sy(end), cx + bw / 4, sy(end),
                              fill=BLUE, width=2, tags=tag)
            c.create_rectangle(cx - bw / 2, sy(q3), cx + bw / 2, sy(q1),
                               fill=theme.SURFACE, outline=BLUE, width=2, tags=tag)
            c.create_line(cx - bw / 2, sy(q2), cx + bw / 2, sy(q2),
                          fill=theme.TEXT, width=3, tags=tag)
            for v in t:
                if v < lo or v > hi:
                    c.create_oval(cx - dot, sy(v) - dot, cx + dot, sy(v) + dot,
                                  outline=BLUE, width=2, tags=tag)
            self.text(c, cx, base + 8 * self.k,
                      f"Round {r}" if len(stats) <= 6 else f"R{r}",
                      fill=theme.MUTED, anchor="n")
            self.hover(c, tag, f"Round {r}: {len(t)} timed answers\n"
                       f"median {q2:.2f} s\nmiddle half {q1:.2f}–{q3:.2f} s\n"
                       f"fastest {min(t):.2f} s, slowest {max(t):.2f} s")

    def times_caption(self):
        stats = self.time_stats()
        body = ("Each box shows one round's correct answers, timed from the moment the "
                "photo appeared to your first keystroke. The box holds the middle half of "
                "those times and the white line across it is the median, the typical answer. "
                "The thin lines reach out to the usual range, and dots beyond them are "
                "unusually slow answers. A lower box means quicker recall. A shorter box "
                "means steadier recall.")
        if stats:
            rs = sorted(stats)
            a, b = rs[0], rs[-1]
            ma, mb = stats[a][1][1], stats[b][1][1]
            if a != b:
                trend = "fell" if mb < ma else "rose" if mb > ma else "held"
                body += (f" Your median {trend} from {ma:.2f} s in round {a} to "
                         f"{mb:.2f} s in round {b}.")
            else:
                body += f" Your median in round {a} was {ma:.2f} s."
        return "How quickly each name came to you", body

    # -- 4. hardest faces ---------------------------------------------------------------
    def face_rows(self):
        keys = {e["key"] for e in self.mine}
        return sorted(((theme.difficulty_index(k, self.log), k) for k in keys), reverse=True)

    def faces_chart(self, c, top, bottom):
        rows = self.face_rows()
        cap = self.text(c, 0, top, "½, where a new face starts", theme.SIZE_SMALL,
                        theme.MUTED, anchor="n")
        y = self.bottom(c, cap) + int(8 * self.k)
        # As many faces as fit at a readable size, hardest first.
        min_row = self.line() + 8 * self.k
        rows = rows[:max(1, min(MAX_FACES, int((bottom - y) // min_row)))]
        left = self.pad + max(self.measure(name_of(k)) for _, k in rows) + int(16 * self.k)
        right = self.W - self.pad - self.measure("0.00") - int(12 * self.k)
        half = left + 0.5 * (right - left)
        c.coords(cap, half, top)
        row = min((bottom - y) / len(rows), 2.4 * self.line())
        bar = row * 0.66
        c.create_line(half, y, half, y + row * len(rows), fill=theme.MUTED, dash=(3, 3))
        by_key = collections.defaultdict(list)
        for e in self.mine:
            by_key[e["key"]].append(e)
        for i, (idx, key) in enumerate(rows):
            es, tag, mid = by_key[key], f"face{i}", y + row / 2
            self.text(c, left - 14 * self.k, mid, name_of(key), anchor="e", tags=tag)
            w = idx * (right - left)
            c.create_rectangle(left, mid - bar / 2, left + w, mid + bar / 2,
                               fill=BLUE, outline="", tags=tag)
            self.text(c, left + w + 10 * self.k, mid, f"{idx:.2f}", fill=theme.MUTED,
                      anchor="w")
            t = clean_seconds(es)
            n = collections.Counter(e["result"] for e in es)
            self.hover(c, tag, f"{name_of(key)}: {len(es)} tries\n"
                       f"missed or skipped {n['miss'] + n['skip']}, "
                       f"slow or hint {n['slow'] + n['hint']}\n"
                       + (f"median {statistics.median(t):.2f} s" if t else "no timed answers"))
            y += row

    def faces_caption(self):
        rows = self.face_rows()
        marks = theme.load_difficulty()
        idx, key = rows[0]
        times = self.copies(key, marks, self.log)
        body = ("The bar is the game's measure of how hard each face is for you, from 0 "
                "(easy) to 1 (hard). A miss or skip counts as a full miss, a slow answer or a "
                "hint as half, and recent rounds count more than old ones, so a face you have "
                "since learned drifts down. A face with no tries starts at ½, the dotted "
                "line. The index sets how often a face comes up in a round: below ⅓ once, "
                "below ⅔ twice, above that three times. "
                f"Your hardest face now is {name_of(key)} at {idx:.2f}, "
                f"which comes up {'once' if times == 1 else f'{times} times'} a round.")
        return "Which faces the game is drilling", body

    # -- 5. mix-ups ------------------------------------------------------------------------
    def mixup_pairs(self):
        names = {}
        for e in self.mine:
            n = name_of(e["key"])
            names.setdefault(n.split()[0].lower(), set()).add(n)
            names.setdefault(n.lower(), set()).add(n)
        pairs = collections.Counter()
        for e in self.mine:
            typed = (e.get("typed") or "").strip().lower()
            if e["result"] != "miss" or not typed:
                continue
            meant = names.get(typed) or names.get(typed.split()[0], set())
            for other in meant - {name_of(e["key"])}:
                pairs[(name_of(e["key"]), other)] += 1
        return pairs

    def mixups(self, c, top, bottom):
        pairs = self.mixup_pairs()
        if not pairs:
            self.text(c, self.pad, top, "None yet.", theme.SIZE_LABEL, theme.MUTED)
            return
        shown = pairs.most_common(10)
        size = theme.SIZE_LABEL
        col = self.pad + max(self.measure(f, size, "bold") for (f, _), _ in shown) \
            + int(30 * self.k)
        self.text(c, self.pad, top, "The face", theme.SIZE_SMALL, theme.MUTED)
        self.text(c, col, top, "You answered", theme.SIZE_SMALL, theme.MUTED)
        t = self.text(c, self.W - self.pad, top, "Times", theme.SIZE_SMALL, theme.MUTED,
                      anchor="ne")
        y = self.bottom(c, t) + int(10 * self.k)
        for (face, typed), n in shown:
            if y + self.line(size) > bottom:
                break
            self.text(c, self.pad, y, face, size, weight="bold")
            self.text(c, col, y, typed, size)
            t = self.text(c, self.W - self.pad, y, f"{n}", size, theme.MUTED, anchor="ne")
            y = self.bottom(c, t) + int(12 * self.k)

    def mixups_caption(self):
        pairs = self.mixup_pairs()
        body = ("A mix-up is a wrong answer that was another person's name in this class, "
                "matched on the first name or the whole name. The left column is the face "
                "on screen, the middle what you typed for it. ")
        if pairs:
            (face, typed), n = pairs.most_common(1)[0]
            body += (f"So far: {plural(sum(pairs.values()), 'mix-up')}. The most common is "
                     f"answering {typed} for {face}"
                     + (f", {n} times." if n > 1 else "."))
        else:
            body += "You have no mix-ups yet."
        return "Who you took for whom", body
