# ==========================================================
# DICOM Toolbox - app to manage DICOM files
# Author: Marcin Leśniak, PhD
#
# Helper functions
# ==========================================================
from pathlib import Path
import sys

# === Use this function when running PY ===
#
def resource_path(relative_path):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path


# === Use this function when running EXE ===

# def resource_path(relative_path):
#     if getattr(sys, "frozen", False):
#         base_path = Path(sys.executable).parent
#     else:
#         base_path = Path(__file__).resolve().parent

#     return base_path / relative_path
