import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
TEST_DIR = os.path.join(ROOT_DIR, "tests")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)