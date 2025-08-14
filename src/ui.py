import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from data_loader import load_json, list_skill_names_for_rarity
from filters import (
    NONE_TOKEN,
    combos_for_rarity,
    compute_max_slots,
    filter_combos,
    options_per_position,
    rarity_label_for_position,
    aggregated_results,
)

class SlotRow(ttk.Frame):
    """A self-contained row for selecting a skill in a specific slot."""
    def __init__(self, master, row_index: int, search_var: tk.StringVar, skill_var: tk.StringVar,
                 on_search_update, on_skill_select, on_combo_open, **kwargs):
        super().__init__(master, **kwargs)
        self.row_index: int = row_index
        self.count_var: tk.StringVar = tk.StringVar(value="0 choices")

        # --- Widget Creation ---
        ttk.Label(self, text=f"Slot {self.row_index + 1}:").pack(side=tk.LEFT)
        self.rarity_details_label = ttk.Label(self, text="(rarity: —)", foreground="#666")
        self.rarity_details_label.pack(side=tk.LEFT, padx=(6, 12))

        search_entry = ttk.Entry(self, textvariable=search_var, width=24)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind("<KeyRelease>", on_search_update)

        ttk.Label(self, text=" ").pack(side=tk.LEFT, padx=4)

        self.combo = ttk.Combobox(self, textvariable=skill_var, width=40, state="readonly", postcommand=on_combo_open)
        self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo.bind("<<ComboboxSelected>>", on_skill_select)

        lbl = ttk.Label(self, textvariable=self.count_var, width=12, anchor=tk.W)
        lbl.pack(side=tk.LEFT, padx=(8, 0))

    def set_options(self, options: List[str]):
        """Sets the dropdown options for the combobox and updates the count."""
        self.combo["values"] = options
        self.count_var.set(f"{len(options)} choices")

    def set_rarity_label(self, label_text: str):
        """Updates the rarity details label."""
        self.rarity_details_label.config(text=f"(rarity: {label_text})")


class CharmCombo(tk.Tk):
    def __init__(self, json_path: str):
        super().__init__()
        self.title("Charm Checker")
        self.geometry("1000x700")

        self.json_path = json_path
        try:
            self.data: Dict[str, Any] = load_json(json_path)
        except Exception as e:
            messagebox.showerror("Load error", f"Failed to load {json_path}:\n{e}")
            raise

        self.selected_rarity = tk.StringVar(value="")
        self.global_search = tk.StringVar(value="")

        self.slot_rows: List[SlotRow] = []
        self.per_dropdown_search: List[tk.StringVar] = []
        self.selected_skills_vars: List[tk.StringVar] = []

        self.combos_current: List[Dict[str, Any]] = []
        self.filtered_current: List[Dict[str, Any]] = []
        self.options_current: List[List[str]] = []

        self._build_layout()
        self._init_rarity_options()

    # ---------- UI setup ----------
    def _build_layout(self):
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(outer)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Rarity:").pack(side=tk.LEFT)
        self.rarity_cb = ttk.Combobox(top, state="readonly", width=12)
        self.rarity_cb.bind("<<ComboboxSelected>>", self.on_rarity_change)
        self.rarity_cb.pack(side=tk.LEFT, padx=(6, 20))

        ttk.Label(top, text="Global search:").pack(side=tk.LEFT)
        gs = ttk.Entry(top, textvariable=self.global_search, width=32)
        gs.pack(side=tk.LEFT, padx=6)
        gs.bind("<KeyRelease>", lambda e: self._refresh_all())
        
        reset_btn = ttk.Button(top, text="Reset Filters", command=self._reset_all_filters)
        reset_btn.pack(side=tk.LEFT, padx=(10, 0))

        mid = ttk.Frame(outer)
        mid.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        left = ttk.LabelFrame(mid, text="Selectors", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.LabelFrame(mid, text="Matching combinations", padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.slots_container = ttk.Frame(left)
        self.slots_container.pack(fill=tk.BOTH, expand=True)

        self.combos_tree = ttk.Treeview(right, columns=("pattern",), show="headings", height=16)
        self.combos_tree.heading("pattern", text="Rarity pattern")
        self.combos_tree.column("pattern", width=350, anchor=tk.W)
        self.combos_tree.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.LabelFrame(outer, text="Aggregated result (when fully selected)", padding=10)
        bottom.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.results_text = tk.Text(bottom, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.configure(state=tk.DISABLED)

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(outer, textvariable=self.status_var, anchor=tk.W)
        status.pack(fill=tk.X, pady=(6, 0))

    def _init_rarity_options(self):
        rarity_keys = sorted(self.data.get("rarity", {}).keys(), key=lambda x: int(x))
        self.rarity_cb["values"] = rarity_keys
        if rarity_keys:
            self.rarity_cb.set(rarity_keys[0])
            self.on_rarity_change()

    # ---------- Event handlers ----------
    def _reset_all_filters(self):
        """Resets all filters to their default state for the current rarity."""
        self.global_search.set("")
        for v in self.per_dropdown_search:
            v.set("")
        for v in self.selected_skills_vars:
            v.set("")
        self._refresh_all()
        
    def on_rarity_change(self, event=None):
        self.selected_rarity.set(self.rarity_cb.get())
        self.combos_current = combos_for_rarity(self.data, self.selected_rarity.get())
        max_slots = compute_max_slots(self.combos_current)

        for row_widget in self.slot_rows:
            row_widget.destroy()
        self.slot_rows = []
        self.per_dropdown_search = []
        self.selected_skills_vars = []

        for i in range(max_slots):
            self._add_slot_row(i)

        self._refresh_all()

    def on_skill_select(self, event, changed_index: int):
        """Callback when a skill is selected. Clears subsequent skill selections."""
        for i in range(changed_index + 1, len(self.selected_skills_vars)):
            self.selected_skills_vars[i].set("")
        self._refresh_all()

    def _add_slot_row(self, idx: int):
        search_var = tk.StringVar(value="")
        self.per_dropdown_search.append(search_var)

        skill_var = tk.StringVar(value="")
        self.selected_skills_vars.append(skill_var)

        row = SlotRow(
            self.slots_container,
            idx,
            search_var=search_var,
            skill_var=skill_var,
            on_search_update=lambda e, i=idx: self._update_slot_options(i),
            on_skill_select=lambda e, i=idx: self.on_skill_select(e, i),
            on_combo_open=lambda i=idx: self._update_slot_options(i)
        )
        row.pack(fill=tk.X, pady=4)
        self.slot_rows.append(row)

    def _refresh_all(self):
        selected_skills = [v.get() if v.get() else None for v in self.selected_skills_vars]
        gsearch = self.global_search.get()
        
        # Translate UI-facing "— none —" to the internal token for the filter logic
        internal_selections = [NONE_TOKEN if s == "— none —" else s for s in selected_skills]
        
        self.filtered_current = filter_combos(self.data, self.combos_current, internal_selections, gsearch)
        self.options_current = options_per_position(self.data, self.filtered_current, len(self.selected_skills_vars))
        
        for i, row in enumerate(self.slot_rows):
            initial_rarity_lbl = rarity_label_for_position(self.combos_current, i)
            row.set_rarity_label(initial_rarity_lbl)
            self._update_slot_options(i)

        self._refresh_combos_tree()
        self._refresh_results(selected_skills)
        self.status_var.set(f"{len(self.filtered_current)} combos match current filters")

    def _update_slot_options(self, idx: int):
        if idx >= len(self.options_current) or idx >= len(self.slot_rows):
            return
        options = list(self.options_current[idx])
        term = (self.per_dropdown_search[idx].get() or "").strip().lower()
        if term:
            def keep(opt: str) -> bool:
                if opt == NONE_TOKEN:
                    return "none".startswith(term) or term in "none"
                return term in opt.lower()
            options = [o for o in options if keep(o)]

        display_opts = ["— none —" if o == NONE_TOKEN else o for o in options]
        
        row = self.slot_rows[idx]
        row.set_options(display_opts)

    def _refresh_combos_tree(self):
        self.combos_tree.delete(*self.combos_tree.get_children())
        for i, c in enumerate(self.filtered_current):
            pattern = str(c.get("combination", []))
            self.combos_tree.insert("", tk.END, values=(pattern,))

    def _refresh_results(self, selected_skills: List[Any]):
        res = aggregated_results(self.data, self.filtered_current, [
            None if (v is None or v == "") else (NONE_TOKEN if v == "— none —" else v)
            for v in selected_skills
        ])
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        if not res:
            self.results_text.insert(tk.END, "Select every non-empty slot to compute aggregated skill levels.\n")
        else:
            for idx, r in enumerate(res, start=1):
                self.results_text.insert(tk.END, f"Result #{idx}\n")
                self.results_text.insert(tk.END, f"  Pattern: {r['combo']}\n")
                totals = r.get("totals", {})
                if not totals:
                    self.results_text.insert(tk.END, "  (no skills)\n\n")
                else:
                    for name, lvl in sorted(totals.items()):
                        self.results_text.insert(tk.END, f"  {name}: level {lvl}\n")
                    self.results_text.insert(tk.END, "\n")
        self.results_text.configure(state=tk.DISABLED)