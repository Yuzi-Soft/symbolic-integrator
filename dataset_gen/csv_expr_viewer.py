from __future__ import annotations

import csv
import os
import random
import textwrap
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


class CsvExprViewer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Expression CSV Viewer")
        self.geometry("1200x760")

        self.rows: list[tuple[str, str]] = []
        self.current_path: str = ""

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="Open CSV", command=self.open_csv).pack(side=tk.LEFT)
        ttk.Button(top, text="Prev", command=self.prev_row).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top, text="Next", command=self.next_row).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(top, text="Random", command=self.random_row).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(top, text="Go to #").pack(side=tk.LEFT, padx=(16, 4))
        self.goto_entry = ttk.Entry(top, width=8)
        self.goto_entry.pack(side=tk.LEFT)
        self.goto_entry.bind("<Return>", lambda _event: self.goto_row())
        ttk.Button(top, text="Go", command=self.goto_row).pack(side=tk.LEFT, padx=(4, 0))

        self.wrap_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Wrap lines", variable=self.wrap_var, command=self.refresh_current_row).pack(
            side=tk.RIGHT
        )

        self.status_var = tk.StringVar(value="Load a CSV file to start.")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 0, 10, 8)).pack(fill=tk.X)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=3)
        body.add(right, weight=7)

        self.table = ttk.Treeview(left, columns=("idx", "derivative", "original"), show="headings", height=24)
        self.table.heading("idx", text="#")
        self.table.heading("derivative", text="Derivative (preview)")
        self.table.heading("original", text="Original (preview)")
        self.table.column("idx", width=60, anchor=tk.CENTER, stretch=False)
        self.table.column("derivative", width=240, anchor=tk.W)
        self.table.column("original", width=240, anchor=tk.W)
        self.table.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.table.bind("<<TreeviewSelect>>", self.on_select)

        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=yscroll.set)
        yscroll.pack(fill=tk.Y, side=tk.RIGHT)

        ttk.Label(right, text="Derivative", padding=(4, 0)).pack(anchor=tk.W)
        self.derivative_text = ScrolledText(right, height=14, wrap=tk.WORD, font=("Menlo", 13))
        self.derivative_text.pack(fill=tk.BOTH, expand=True)
        self.derivative_text.configure(state=tk.DISABLED)

        ttk.Label(right, text="Original Function", padding=(4, 8, 4, 0)).pack(anchor=tk.W)
        self.original_text = ScrolledText(right, height=14, wrap=tk.WORD, font=("Menlo", 13))
        self.original_text.pack(fill=tk.BOTH, expand=True)
        self.original_text.configure(state=tk.DISABLED)

    def open_csv(self) -> None:
        initial_dir = os.path.dirname(os.path.abspath(__file__))
        path = filedialog.askopenfilename(
            title="Select CSV file",
            initialdir=initial_dir,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        self.load_csv(path)

    def load_csv(self, path: str) -> None:
        loaded: list[tuple[str, str]] = []
        invalid_lines: list[int] = []

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for line_no, row in enumerate(reader, start=1):
                if len(row) < 2:
                    invalid_lines.append(line_no)
                    continue
                derivative = row[0].strip()
                original = row[1].strip()
                if derivative == "" or original == "":
                    invalid_lines.append(line_no)
                    continue
                loaded.append((derivative, original))

        if len(loaded) == 0:
            messagebox.showerror("Load failed", "No valid rows found. CSV should contain at least two columns.")
            return

        self.rows = loaded
        self.current_path = path
        self._reload_table()

        duplicate_count = len(self.rows) - len(set(self.rows))
        status = f"{os.path.basename(path)} | rows={len(self.rows)} | duplicates={duplicate_count}"
        if invalid_lines:
            status += f" | skipped invalid lines={len(invalid_lines)}"
        self.status_var.set(status)

    def _reload_table(self) -> None:
        for iid in self.table.get_children():
            self.table.delete(iid)

        for idx, (derivative, original) in enumerate(self.rows, start=1):
            self.table.insert(
                "",
                tk.END,
                iid=str(idx - 1),
                values=(idx, self._preview(derivative), self._preview(original)),
            )

        if self.rows:
            self.table.selection_set("0")
            self.table.focus("0")
            self.table.see("0")
            self._show_row(0)

    def on_select(self, _event: object) -> None:
        selected = self.table.selection()
        if not selected:
            return
        row_index = int(selected[0])
        self._show_row(row_index)

    def _show_row(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self.rows):
            return
        derivative, original = self.rows[row_index]
        self._set_text(self.derivative_text, self._format_expr(derivative))
        self._set_text(self.original_text, self._format_expr(original))
        file_name = os.path.basename(self.current_path) if self.current_path else ""
        self.status_var.set(f"{file_name} | row {row_index + 1}/{len(self.rows)}")

    def refresh_current_row(self) -> None:
        selected = self.table.selection()
        if not selected:
            return
        self._show_row(int(selected[0]))

    def prev_row(self) -> None:
        self._move_selection(-1)

    def next_row(self) -> None:
        self._move_selection(1)

    def random_row(self) -> None:
        if not self.rows:
            return
        idx = random.randint(0, len(self.rows) - 1)
        self._select_row(idx)

    def goto_row(self) -> None:
        if not self.rows:
            return
        try:
            idx_1_based = int(self.goto_entry.get().strip())
        except ValueError:
            messagebox.showinfo("Invalid index", "Please enter a valid integer row number.")
            return
        idx = idx_1_based - 1
        if idx < 0 or idx >= len(self.rows):
            messagebox.showinfo("Out of range", f"Row must be between 1 and {len(self.rows)}.")
            return
        self._select_row(idx)

    def _move_selection(self, delta: int) -> None:
        if not self.rows:
            return
        selected = self.table.selection()
        if not selected:
            self._select_row(0)
            return
        current = int(selected[0])
        nxt = max(0, min(len(self.rows) - 1, current + delta))
        self._select_row(nxt)

    def _select_row(self, row_index: int) -> None:
        iid = str(row_index)
        self.table.selection_set(iid)
        self.table.focus(iid)
        self.table.see(iid)
        self._show_row(row_index)

    def _set_text(self, widget: ScrolledText, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state=tk.DISABLED)

    def _preview(self, s: str, width: int = 38) -> str:
        return s if len(s) <= width else s[: width - 3] + "..."

    def _format_expr(self, expr: str) -> str:
        if not self.wrap_var.get():
            return expr
        wrapped = textwrap.fill(expr, width=78, break_long_words=False, break_on_hyphens=False)
        return wrapped


def main() -> None:
    app = CsvExprViewer()
    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple.csv")
    if os.path.exists(default_path):
        app.load_csv(default_path)
    app.mainloop()


if __name__ == "__main__":
    main()
