import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as sd
import tkinter.filedialog as fd
import random
import time
import json
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Local persistence file
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "hk_typer_leaderboard.json")

# Theme / styling
THEME = {
    "bg": "#0f1115",
    "panel": "#15161a",
    "muted": "#7a7d82",
    "text": "#d8d8d8",
    "accent": "#ffb4d9",
    "accent2": "#7dd3fc",
    "error": "#ff6b6b",
    "font": "Consolas",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class SpeedTyperApp(ctk.CTk):
    """HK Typer - Silent Edition (No Audio)"""

    def __init__(self):
        super().__init__()
        self.title("HK Typer — Silent Edition")
        self.geometry("1100x720")
        self.configure(fg_color=THEME["bg"])

        # State
        self.time_limit = 30
        self.running = False
        self.paused = False
        self.start_time = None
        self.wpm_history = []
        self.target_text = ""
        self.current_pos = 0
        self.typed_attempts = 0
        self.correct_chars = 0
        self.history_chars = []
        self.longest_correct_word_streak = 0
        self.current_word_streak = 0

        # Activity indicator
        self.activity_state = "idle"  # idle, dancing, fallen

        # Text sources
        self.word_bank = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
            "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
            "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
            "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "python", "code", "program", "syntax", "variable", "function", "class",
            "import", "return", "print", "while", "for", "logic", "design", "data"
        ]
        self.sentence_bank = [
            "Practice makes progress and small steps lead to big gains.",
            "Clean code is not written, it is rewritten many times.",
            "Focus on accuracy then speed will follow naturally.",
            "Use consistent naming and keep functions single-purpose.",
            "Typing quickly is a skill built from repetition and good technique."
        ]

        self.build_ui()
        self.reset_game()

    def build_ui(self):
        # Header with controls and mode selection
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=10)

        logo = ctk.CTkLabel(header, text="HK Typer ♡", font=(THEME["font"], 22, "bold"),
                            text_color=THEME["accent"])
        logo.pack(side="left")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")

        # Mode menu (timed, words, practice)
        self.mode_menu = ctk.CTkOptionMenu(controls, values=["Timed", "Words", "Practice"],
                                           command=self._set_mode, width=110)
        self.mode_menu.set("Timed")
        self.mode_menu.pack(side="left", padx=(0, 8))

        self.time_menu = ctk.CTkOptionMenu(controls, values=["15", "30", "60", "120"],
                                           command=self._set_time, width=70)
        self.time_menu.set(str(self.time_limit))
        self.time_menu.pack(side="left", padx=(0, 8))

        self.start_btn = ctk.CTkButton(controls, text="Start", command=self.start_with_countdown,
                                       fg_color=THEME["panel"], width=100)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.pause_btn = ctk.CTkButton(controls, text="Pause", command=self.toggle_pause,
                                       fg_color=THEME["panel"], width=80)
        self.pause_btn.pack(side="left", padx=(0, 8))

        self.reset_btn = ctk.CTkButton(controls, text="Reset", command=self.reset_game,
                                       fg_color=THEME["panel"], width=80)
        self.reset_btn.pack(side="left")

        # Stats Row
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=16, pady=(6, 10))

        self.wpm_label = ctk.CTkLabel(stats, text="WPM: 0", font=(THEME["font"], 18),
                                      text_color=THEME["text"])
        self.wpm_label.pack(side="left", padx=8)

        self.acc_label = ctk.CTkLabel(stats, text="Acc: 0%", font=(THEME["font"], 18),
                                      text_color=THEME["text"])
        self.acc_label.pack(side="left", padx=8)

        self.streak_label = ctk.CTkLabel(stats, text="Streak: 0", font=(THEME["font"], 16),
                                         text_color=THEME["accent2"])
        self.streak_label.pack(side="left", padx=8)

        # Progress bar for time elapsed
        self.time_bar = ctk.CTkProgressBar(stats, width=300)
        self.time_bar.set(0)
        self.time_bar.pack(side="right", padx=12)

        # Main frame with text area and right panel (activity indicator)
        main = ctk.CTkFrame(self, fg_color=THEME["panel"])
        main.pack(expand=True, fill="both", padx=16, pady=12)

        # Right panel for activity indicator and small controls
        right_panel = ctk.CTkFrame(main, width=220, fg_color=THEME["panel"])
        right_panel.pack(side="right", fill="y", padx=(8, 0), pady=6)

        # Activity label used instead of dancer
        self.activity_label = ctk.CTkLabel(right_panel, text="Idle", font=(THEME["font"], 16),
                                           text_color=THEME["muted"])
        self.activity_label.pack(padx=12, pady=60)

        # Small settings below activity indicator
        settings_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        settings_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.font_size_menu = ctk.CTkOptionMenu(settings_frame, values=["14", "16", "18", "20", "22"],
                                                command=self._set_font_size, width=80)
        self.font_size_menu.set("20")
        self.font_size_menu.pack(side="left", padx=(4, 4))
        self.export_btn = ctk.CTkButton(settings_frame, text="Export", command=self.export_results, width=80)
        self.export_btn.pack(side="right", padx=(4, 4))

        # Text area (readonly, per-character tags)
        self.text_area = tk.Text(main, font=(THEME["font"], 20), bg=THEME["panel"],
                                 fg=THEME["text"], wrap="word", borderwidth=0,
                                 highlightthickness=0, padx=14, pady=14, relief="flat")
        self.text_area.pack(expand=True, fill="both")
        self.text_area.tag_config("correct", foreground=THEME["accent2"])
        self.text_area.tag_config("wrong", foreground=THEME["error"])
        self.text_area.tag_config("current", background="#222428", foreground=THEME["text"])
        self.text_area.configure(state="disabled")

        # Footer: live graph area
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 12))
        self.graph_canvas_holder = ctk.CTkFrame(footer, fg_color="transparent")
        self.graph_canvas_holder.pack(side="left", fill="both", expand=True)
        self.leaderboard_btn = ctk.CTkButton(footer, text="Leaderboard", command=self.show_leaderboard, width=120)
        self.leaderboard_btn.pack(side="right", padx=12)

        # Bind keystrokes for capture
        self.bind_all("<Key>", self.on_key, add=True)

    def _set_mode(self, choice):
        self.mode = choice

    def _set_time(self, choice):
        try:
            self.time_limit = int(choice)
        except Exception:
            pass
        self.time_bar.set(0)

    def _set_font_size(self, choice):
        try:
            size = int(choice)
            self.text_area.configure(font=(THEME["font"], size))
        except Exception:
            pass

    def _set_activity(self, state):
        """Update activity indicator (replaces dancer)."""
        self.activity_state = state
        if state == "dancing":
            self.activity_label.configure(text="♪ Dancing", text_color=THEME["accent2"])
        elif state == "fallen":
            self.activity_label.configure(text="× Fallen", text_color=THEME["error"])
        else:
            self.activity_label.configure(text="Idle", text_color=THEME["muted"])

    def start_with_countdown(self):
        """Start with 3..1 countdown overlay for readiness."""
        if self.running:
            # restart requested
            self.reset_game()
        # overlay background must be a valid color (Tk does not accept alpha hex)
        overlay = tk.Label(self.text_area, text="", bg=THEME["panel"], fg="white", font=(THEME["font"], 36))
        overlay.place(relx=0.5, rely=0.45, anchor="center")
        self.update()
        def countdown(i):
            if i == 0:
                overlay.destroy()
                self.start_test()
                return
            overlay.configure(text=str(i))
            self.after(700, lambda: countdown(i - 1))
        countdown(3)

    def start_test(self):
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self.wpm_history = []
        self.current_pos = 0
        self.typed_attempts = 0
        self.correct_chars = 0
        self.history_chars = []
        self.current_word_streak = 0
        self._set_current_tag(0)
        self._set_activity("dancing")
        self._tick()

    def reset_game(self):
        """Reset all state and regenerate target text."""
        self.running = False
        self.paused = False
        self.start_time = None
        self.wpm_history = []
        self.current_pos = 0
        self.typed_attempts = 0
        self.correct_chars = 0
        self.history_chars = []
        self.time_bar.set(0)
        self.wpm_label.configure(text="WPM: 0")
        self.acc_label.configure(text="Acc: 0%")
        self.streak_label.configure(text="Streak: 0")
        self._set_activity("idle")

        # determine mode and generate text
        mode = getattr(self, "mode", "Timed")
        if mode == "Timed":
            random_words = random.choices(self.word_bank, k=120)
            # add punctuation for interest
            for i in range(6):
                idx = (i * 19) % len(random_words)
                random_words[idx] = random_words[idx] + ('.' if i % 2 == 0 else '!')
            self.target_text = " ".join(random_words)
        elif mode == "Words":
            # words mode: short list of words equal to time_limit as count when starting
            count = max(20, self.time_limit)
            self.target_text = " ".join(random.choices(self.word_bank, k=count))
        else:  # Practice
            self.target_text = random.choice(self.sentence_bank)

        # populate text_area
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", self.target_text)
        self.text_area.tag_remove("correct", "1.0", "end")
        self.text_area.tag_remove("wrong", "1.0", "end")
        self.text_area.tag_remove("current", "1.0", "end")
        self._set_current_tag(0)
        self.text_area.configure(state="disabled")

        # remove previous graph if present
        for child in self.graph_canvas_holder.winfo_children():
            child.destroy()

    def _index_for_pos(self, pos):
        return f"1.0 + {pos} chars"

    def _set_current_tag(self, pos):
        self.text_area.configure(state="normal")
        self.text_area.tag_remove("current", "1.0", "end")
        if 0 <= pos < len(self.target_text):
            start = self._index_for_pos(pos)
            end = self._index_for_pos(pos + 1)
            self.text_area.tag_add("current", start, end)
            self.text_area.see(start)
        self.text_area.configure(state="disabled")

    def on_key(self, event):
        """Global key handler that simulates typed input behavior like modern speed-test UIs."""
        if event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
                            "Caps_Lock", "Tab", "Meta_L", "Meta_R", "Escape"):
            return

        # Pause toggle via Escape
        if event.keysym == "Escape":
            self.toggle_pause()
            return "break"

        if not self.running and event.keysym not in ("Escape",):
            # Ignore keystrokes until start pressed (or countdown finished)
            return

        if self.paused:
            return "break"

        if event.keysym == "BackSpace":
            self._handle_backspace()
            return "break"
        if event.keysym == "Return":
            typed = "\n"
        else:
            typed = event.char

        if typed == "" or not typed.isprintable() or event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock", "Tab", "Meta_L", "Meta_R"):
            return "break"

        if self.current_pos >= len(self.target_text):
            return "break"

        expected = self.target_text[self.current_pos]
        start = self._index_for_pos(self.current_pos)
        end = self._index_for_pos(self.current_pos + 1)

        self.text_area.configure(state="normal")
        correct = typed == expected
        if correct:
            self.text_area.tag_add("correct", start, end)
            self.correct_chars += 1
        else:
            self.text_area.tag_add("wrong", start, end)

        self.history_chars.append({"char": typed, "expected": expected, "correct": correct})
        self.typed_attempts += 1
        self.current_pos += 1
        self._set_current_tag(self.current_pos)
        self.text_area.configure(state="disabled")

        # word completion handling
        if typed == " " or (correct and typed in ".!?"):
            # compute last word correctness
            word_end = self.current_pos - 1 if typed == " " else self.current_pos
            prev_space = self.target_text.rfind(" ", 0, word_end)
            word_start = prev_space + 1
            # slice history corresponding to that word
            # history_chars is by character; ensure indices valid
            word_hist = self.history_chars[word_start:word_end]
            any_wrong = any(not h.get("correct", False) for h in word_hist) if word_hist else False
            if any_wrong:
                # fail behavior: mark fallen
                self._set_activity("fallen")
                self.current_word_streak = 0
            else:
                # correct word
                self._set_activity("dancing")
                self.current_word_streak += 1
                self.longest_correct_word_streak = max(self.longest_correct_word_streak, self.current_word_streak)
            self.streak_label.configure(text=f"Streak: {self.current_word_streak}")

        return "break"

    def _handle_backspace(self):
        if self.current_pos == 0:
            return
        last = self.history_chars.pop()
        self.current_pos -= 1
        if last.get("correct"):
            self.correct_chars = max(0, self.correct_chars - 1)
        self.typed_attempts = max(0, self.typed_attempts - 1)

        start = self._index_for_pos(self.current_pos)
        end = self._index_for_pos(self.current_pos + 1)
        self.text_area.configure(state="normal")
        self.text_area.tag_remove("correct", start, end)
        self.text_area.tag_remove("wrong", start, end)
        self._set_current_tag(self.current_pos)
        self.text_area.configure(state="disabled")

        # if we were in fallen state, allow return to dancing when the current word is corrected fully
        if self.activity_state == "fallen":
            prev_space = self.target_text.rfind(" ", 0, self.current_pos)
            word_start = prev_space + 1
            next_space = self.target_text.find(" ", self.current_pos)
            word_end = next_space if next_space != -1 else len(self.target_text)
            # Check if we have all characters for that word in history and none wrong
            if len(self.history_chars) >= word_end:
                word_hist = self.history_chars[word_start:word_end]
                any_wrong = any(not h.get("correct", False) for h in word_hist) if word_hist else False
                if not any_wrong:
                    self._set_activity("dancing")

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.configure(text="Resume")
            # stop activity indicator
            self._set_activity("idle")
        else:
            self.pause_btn.configure(text="Pause")
            self._set_activity("dancing")

    def _tick(self):
        """Periodic update every 250ms while running: update WPM history, UI and time bar."""
        if not self.running or self.paused:
            # schedule continue even when paused to resume updates when unpaused
            if self.running and self.paused:
                self.after(250, self._tick)
            return
        elapsed = time.time() - self.start_time
        elapsed_seconds = max(1, elapsed)
        current_wpm = (self.correct_chars / 5) / (elapsed_seconds / 60)
        acc = int((self.correct_chars / self.typed_attempts) * 100) if self.typed_attempts > 0 else 0

        self.wpm_label.configure(text=f"WPM: {int(current_wpm)}")
        self.acc_label.configure(text=f"Acc: {acc}%")
        self.time_bar.set(min(1.0, elapsed / self.time_limit))

        # append to history roughly once per second
        if int(elapsed) == 0 or (not self.wpm_history) or (len(self.wpm_history) < int(elapsed)):
            self.wpm_history.append(current_wpm)

        if elapsed >= self.time_limit:
            self.finish_test()
            return
        self.after(250, self._tick)

    def finish_test(self):
        self.running = False
        elapsed_min = self.time_limit / 60
        gross_wpm = (self.correct_chars / 5) / elapsed_min if elapsed_min > 0 else 0
        errors = max(0, self.typed_attempts - self.correct_chars)
        net_wpm = gross_wpm - (errors / elapsed_min) if elapsed_min > 0 else 0
        net_wpm = max(0, net_wpm)
        accuracy = int(((self.correct_chars) / self.typed_attempts) * 100) if self.typed_attempts > 0 else 0

        # overlay results and graph
        for child in self.graph_canvas_holder.winfo_children():
            child.destroy()

        result_label = ctk.CTkLabel(self.graph_canvas_holder,
                                    text=f"Net WPM: {int(net_wpm)}   Acc: {accuracy}%   Raw: {int(gross_wpm)}",
                                    font=(THEME["font"], 16),
                                    text_color=THEME["accent"])
        result_label.pack(pady=4)

        # show improvements / achievements
        ach_text = f"Best streak: {self.longest_correct_word_streak}"
        ach_label = ctk.CTkLabel(self.graph_canvas_holder, text=ach_text, text_color=THEME["accent2"])
        ach_label.pack()

        self._plot_graph()
        # prompt for leaderboard name
        name = sd.askstring("Save result", "Enter your name for leaderboard (optional):")
        if name:
            self._save_leaderboard(name, int(net_wpm), accuracy)

    def _plot_graph(self):
        data = self.wpm_history if self.wpm_history else [0]
        fig, ax = plt.subplots(figsize=(6, 2.0), dpi=100)
        fig.patch.set_facecolor(THEME["bg"])
        ax.set_facecolor(THEME["bg"])
        ax.plot(data, color=THEME["accent2"], linewidth=2)
        ax.fill_between(range(len(data)), data, color=THEME["accent2"], alpha=0.12)
        ax.tick_params(colors=THEME["muted"])
        for spine in ax.spines.values():
            spine.set_color(THEME["muted"])
        ax.set_xlabel("s", color=THEME["muted"])
        ax.set_ylabel("WPM", color=THEME["muted"])
        canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _save_leaderboard(self, name, wpm, acc):
        try:
            data = []
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            entry = {"name": name, "wpm": int(wpm), "acc": int(acc), "time": int(time.time())}
            data.append(entry)
            data = sorted(data, key=lambda x: x["wpm"], reverse=True)[:50]
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def show_leaderboard(self):
        # read leaderboard file and show in simple dialog
        data = []
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []
        text = "Leaderboard (Top 20):\n\n"
        for i, e in enumerate(data[:20], 1):
            text += f"{i}. {e.get('name','-')} — {e.get('wpm',0)} WPM  ({e.get('acc',0)}%)\n"
        messagebox.showinfo("Leaderboard", text)

    def export_results(self):
        # Export last session summary to CSV
        filepath = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            # gather summary
            elapsed_min = max(1e-6, self.time_limit / 60)
            gross_wpm = (self.correct_chars / 5) / elapsed_min
            errors = max(0, self.typed_attempts - self.correct_chars)
            net_wpm = gross_wpm - (errors / elapsed_min)
            accuracy = int(((self.correct_chars) / self.typed_attempts) * 100) if self.typed_attempts > 0 else 0
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("net_wpm,raw_wpm,accuracy,typed,correct,streak\n")
                f.write(f"{int(net_wpm)},{int(gross_wpm)},{accuracy},{self.typed_attempts},{self.correct_chars},{self.longest_correct_word_streak}\n")
            messagebox.showinfo("Export", "Exported results.")
        except Exception:
            messagebox.showerror("Export", "Failed to export results.")


if __name__ == "__main__":
    app = SpeedTyperApp()
    app.mainloop()