from typing import Any, Dict, List, Tuple

from data_loader import list_skill_names_for_rarity, lookup_level


NONE_TOKEN = "__NONE__"


def combos_for_rarity(data: Dict[str, Any], selected_rarity: str) -> List[Dict[str, Any]]:
    if not data or not selected_rarity:
        return []
    return list((data.get("rarity", {}).get(str(selected_rarity), [])))


def compute_max_slots(combos: List[Dict[str, Any]]) -> int:
    max_len = 0
    for c in combos:
        comb = c.get("combination", [])
        if len(comb) > max_len:
            max_len = len(comb)
    return max_len


def filter_combos(
    data: Dict[str, Any],
    all_combos: List[Dict[str, Any]],
    selected_skills: List[Any],
    global_search: str,
) -> List[Dict[str, Any]]:
    if not all_combos:
        return []
    sterm = (global_search or "").strip().lower()

    def combo_passes(c: Dict[str, Any]) -> bool:
        combo = c.get("combination", [])

        # Global search: at least one skill across all slots contains the term
        if sterm:
            any_match = False
            for rnum in combo:
                if rnum is None:
                    continue
                for s in data["skills_data"].get(str(rnum), []):
                    if sterm in s.get("skill_name", "").lower():
                        any_match = True
                        break
                if any_match:
                    break
            if not any_match:
                return False

        # Per-slot selection filtering
        for idx, sel in enumerate(selected_skills):
            if not sel:
                continue
            rnum = combo[idx] if idx < len(combo) else None
            if sel == NONE_TOKEN:
                if rnum is not None:
                    return False
                continue
            if rnum is None:
                return False
            names = list_skill_names_for_rarity(data, str(rnum))
            if sel not in names:
                return False
        return True

    return [c for c in all_combos if combo_passes(c)]


def options_per_position(
    data: Dict[str, Any], filtered: List[Dict[str, Any]], positions: int
) -> List[List[str]]:
    opts: List[set] = [set() for _ in range(positions)]
    for c in filtered:
        combo = c.get("combination", [])
        for i in range(positions):
            rnum = combo[i] if i < len(combo) else None
            if rnum is None:
                opts[i].add(NONE_TOKEN)
            else:
                for s in data["skills_data"].get(str(rnum), []):
                    name = s.get("skill_name")
                    if name:
                        opts[i].add(name)
    # sort; keep NONE first if present
    out: List[List[str]] = []
    for s in opts:
        arr = sorted([x for x in s if x != NONE_TOKEN], key=lambda x: x.lower())
        if NONE_TOKEN in s:
            arr.insert(0, NONE_TOKEN)
        out.append(arr)
    return out


def rarity_label_for_position(all_combos: List[Dict[str, Any]], pos: int) -> str:
    vals = set()
    for c in all_combos:
        combo = c.get("combination", [])
        r = combo[pos] if pos < len(combo) else None
        vals.add("none" if r is None else str(r))
    return " | ".join(sorted(vals)) if vals else "—"


def aggregated_results(
    data: Dict[str, Any],
    filtered: List[Dict[str, Any]],
    selected_skills: List[Any],
) -> List[Dict[str, Any]]:
    # Show results only if each slot that can be non-null has a selection (not None)
    if not filtered:
        return []

    max_len = max(len(c.get("combination", [])) for c in filtered)
    # If any position has some non-null rnum among the filtered combos but we don't have a selection yet -> not ready
    for i in range(max_len):
        any_nonn = any((c.get("combination", [None]*max_len)[i] is not None) for c in filtered)
        if any_nonn and (i >= len(selected_skills) or not selected_skills[i]):
            return []

    results = []
    for c in filtered:
        combo = c.get("combination", [])
        totals: Dict[str, int] = {}
        for i, sel in enumerate(selected_skills):
            if not sel or sel == NONE_TOKEN:
                continue
            rnum = combo[i] if i < len(combo) else None
            lvl = lookup_level(data, rnum, sel)
            totals[sel] = totals.get(sel, 0) + int(lvl)
        results.append({"combo": combo, "totals": totals})
    return results