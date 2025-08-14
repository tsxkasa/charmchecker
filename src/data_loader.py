import json
from typing import Any, Dict, List


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_skill_names_for_rarity(data_obj: Dict[str, Any], rarity_key: str) -> List[str]:
    if not data_obj or "skills_data" not in data_obj:
        return []
    return [s.get("skill_name") for s in data_obj["skills_data"].get(str(rarity_key), [])]


def lookup_level(data_obj: Dict[str, Any], rarity_number: Any, skill_name: str) -> int:
    if rarity_number is None:
        return 0
    arr = [s for s in data_obj["skills_data"].get(str(rarity_number), []) if s.get("skill_name") == skill_name]
    if not arr:
        return 0
    return max(int(s.get("skill_level", 0)) for s in arr)