import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

DIR2ROOT = Path(__file__).parent.parent.absolute()

DIR2DATA = DIR2ROOT / "data"
DIR2RAW_IJ = DIR2DATA / "ij_cnam" / "raw"
DIR2CLEAN_IJ = DIR2DATA / "ij_cnam" / "clean"

# images
DIR2IMG = DIR2ROOT / "reports" / "img"
DIR2IMG_CNAM = DIR2IMG / "cnam_open_data"

# results
DIR2RESULTS = DIR2ROOT / "results"
