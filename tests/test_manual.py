import sys
import os

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


print("\n--- TEST AI DEMUCS ---")

from project import AudioSeparator

input_test_audio = os.path.join( file_, r"tests\temp\test_audio.wav")

aus = AudioSeparator()

vocal, bgm = aus.separate(input_test_audio)

print("✅ Đã tách xong!")
print(f"👉 File giọng nói nằm ở: {vocal}")
print(f"👉 File nhạc nền nằm ở: {bgm}")