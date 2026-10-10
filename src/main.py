
import runpy
from pathlib import Path

if __name__ == "__main__":
    matcher_path = Path(__file__).parent / "matcher.py"
    runpy.run_path(str(matcher_path), run_name="__main__")
