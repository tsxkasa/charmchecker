from typing import Any, Dict, List, Set, Tuple

from data_loader import get_skills_for_rarity, list_skill_names_for_rarity, lookup_level


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
    selected_levels: List[Any],
    global_search: str,
) -> List[Dict[str, Any]]:
    if not all_combos:
        return []
    sterm = (global_search or "").strip().lower()

    def combo_passes(c: Dict[str, Any]) -> bool:
        combo = c.get("combination", [])

        if sterm:
            any_match = False
            for rnum in combo:
                if rnum is None: continue
                for s in get_skills_for_rarity(data, str(rnum)):
                    if sterm in s.get("skill_name", "").lower():
                        any_match = True
                        break
                if any_match: break
            if not any_match: return False

        for idx, sel in enumerate(selected_skills):
            if not sel: continue
            rnum = combo[idx] if idx < len(combo) else None
            
            if sel == NONE_TOKEN:
                if rnum is not None: return False
                continue
            
            if rnum is None: return False
            
            all_skills_for_rnum = get_skills_for_rarity(data, str(rnum))
            skill_names = [s.get("skill_name") for s in all_skills_for_rnum]
            if sel not in skill_names:
                return False

            sel_level = selected_levels[idx] if idx < len(selected_levels) else None
            if sel_level:
                found_match = False
                for s in all_skills_for_rnum:
                    if s.get("skill_name") == sel and str(s.get("skill_level")) == str(sel_level):
                        found_match = True
                        break
                if not found_match:
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
                for s in get_skills_for_rarity(data, str(rnum)):
                    name = s.get("skill_name")
                    if name:
                        opts[i].add(name)
    out: List[List[str]] = []
    for s in opts:
        arr = sorted([x for x in s if x != NONE_TOKEN], key=lambda x: x.lower())
        if NONE_TOKEN in s:
            arr.insert(0, NONE_TOKEN)
        out.append(arr)
    return out


def get_levels_for_skill_in_slot(
    data: Dict[str, Any],
    filtered_combos: List[Dict[str, Any]],
    slot_index: int,
    skill_name: str,
) -> List[str]:
    if not skill_name or skill_name == NONE_TOKEN:
        return []
    
    possible_levels: Set[str] = set()
    for c in filtered_combos:
        combo = c.get("combination", [])
        if slot_index < len(combo):
            rnum = combo[slot_index]
            if rnum is not None:
                for skill in get_skills_for_rarity(data, str(rnum)):
                    if skill.get("skill_name") == skill_name:
                        possible_levels.add(str(skill.get("skill_level")))
                        
    return sorted(list(possible_levels), key=int)


def rarity_label_for_position(all_combos: List[Dict[str, Any]], pos: int) -> str:
    vals = set()
    for c in all_combos:
        combo = c.get("combination", [])
        r = combo[pos] if pos < len(combo) else None
        vals.add("none" if r is None else str(r))
    return " | ".join(sorted(list(vals))) if vals else "—"


def aggregated_results(
    data: Dict[str, Any],
    filtered: List[Dict[str, Any]],
    selected_skills: List[Any],
) -> List[Dict[str, Any]]:
    if not filtered: return []

    max_len = max((len(c.get("combination", [])) for c in filtered), default=0)
    for i in range(max_len):
        any_non_null = any((c.get("combination", [None] * max_len)[i] is not None) for c in filtered)
        if any_non_null and (i >= len(selected_skills) or not selected_skills[i]):
            return []

    results = []
    for c in filtered:
        combo = c.get("combination", [])
        totals: Dict[str, int] = {}
        for i, sel in enumerate(selected_skills):
            if not sel or sel == NONE_TOKEN: continue
            rnum = combo[i] if i < len(combo) else None
            lvl = lookup_level(data, rnum, sel)
            totals[sel] = totals.get(sel, 0) + int(lvl)
        results.append({"combo": combo, "totals": totals})
    return results