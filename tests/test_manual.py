import sys
import os

from sympy import Segment

# them path để gọi project
file_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if file_ not in sys.path:
    sys.path.append(file_)
# print(file_)

# from project import MediaProcessor

# # khởi tạo
# mp = MediaProcessor()

# # 1. Tạo sẵn các thư mục để chứa file đầu ra (tránh lỗi hệ điều hành không tìm thấy thư mục)
# os.makedirs(r"tests\temp", exist_ok=True)
# os.makedirs("output", exist_ok=True)

# input_video = os.path.join( file_, r"tests\test_videos\test_video_1.mp4")

# print("dang tach audio...")
# mp.extact_audio(input_video, "temp/test_audio.wav")
# print("Tach thanh cong! Hay kiem tra thu muc temp/")

# print("dang ghep moi audio vao video...")
# mp.merge_audio_to_video(input_video, "temp/test_audio.wav", "output/output_test_video.mp4")
# print("✅Ghep thanh cong! Hay kiem tra thu muc output/")


# print("\n--- TEST AI DEMUCS ---")

# from project import AudioSeparator

# input_test_audio = os.path.join( file_, r"tests\temp\test_audio.wav")

# aus = AudioSeparator()

# vocal, bgm = aus.separate(input_test_audio)

# print("✅ Đã tách xong!")
# print(f"👉 File giọng nói nằm ở: {vocal}")
# print(f"👉 File nhạc nền nằm ở: {bgm}")






# ======================================================
# --- ĐANG TEST: AI FASTER-WHISPER (STT) ---
# ======================================================

print("\n--- TEST AI FASTER-WHISPER (STT) ---")

from config import TEMP_DIR
from project import SpeechRecognizer

vocal_path = os.path.join(TEMP_DIR, "separated", "htdemucs", "test_audio", "vocals.wav")
rec = SpeechRecognizer()
segment = rec.transcribe(vocal_path)
print("\n✅ AI ĐÃ NGHE XONG! KẾT QUẢ:")

for s in segment:
    print(f"[{s.start_time: .1f}s - {s.end_time: .1f}s] {s.original_text}")
    






