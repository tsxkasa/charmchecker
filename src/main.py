import sys
import os
from ui import CharmCombo

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    json_file_path = resource_path("extracted_data.json")
    
    app = CharmCombo(json_path=json_file_path)
    app.mainloop()