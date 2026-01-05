import traceback
import sys
from pathlib import Path

# Add the project root to sys.path just in case
sys.path.append(str(Path(__file__).parent.parent))

try:
    print("Attempting to import models...")
    from src.models import Child, Letter
    print("✅ Import successful!")
except Exception:
    print("❌ Import failed with the following traceback:")
    traceback.print_exc()
