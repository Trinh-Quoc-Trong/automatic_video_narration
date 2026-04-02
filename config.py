import os

# config.py nằm ở gốc, nên thư mục chứa nó chính là ROOT_DIR
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Định nghĩa sẵn mọi nẻo đường trong dự án
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
TEST_DIR = os.path.join(ROOT_DIR, "tests")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

# Tự động tạo thư mục nếu chưa có
os.makedirs(TEMP_DIR, exist_ok= True)
os.makedirs(OUTPUT_DIR, exist_ok= True)