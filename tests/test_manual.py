# import sys
# import os

# from sympy import Segment

# # them path để gọi project
# file_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if file_ not in sys.path:
#     sys.path.append(file_)
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

# print("\n--- TEST AI FASTER-WHISPER (STT) ---")

# from config import TEMP_DIR
# from project import SpeechRecognizer

# vocal_path = os.path.join(TEMP_DIR, "separated", "htdemucs", "test_audio", "vocals.wav")
# rec = SpeechRecognizer()
# segment = rec.transcribe(vocal_path)
# print("\n✅ AI ĐÃ NGHE XONG! KẾT QUẢ:")

# for s in segment:
#     print(f"[{s.start_time: .1f}s - {s.end_time: .1f}s] {s.original_text}")
    



# # ======================================================
# # --- ĐANG TEST: AI OLLAMA (DỊCH THUẬT VỚI GEMMA 4) ---
# # ======================================================
# print("\n--- TEST AI OLLAMA (TRANSLATION) ---")

# from project import Translator, SubtitleSegment, SetupManager

# # Đảm bảo model đã được tải về trước khi test
# MODEL_NAME = "gemma4:e4b"
# SetupManager.ensure_model_ready(MODEL_NAME)

# # Dữ liệu giả lập (Mock data)
# test_segments = [
#     SubtitleSegment(0, 3.5, "In this video, we will explore the power of RTX 3060.", ""),
#     SubtitleSegment(4, 8, "It is an incredible GPU for local AI research.", "")
# ]

# t = Translator(model_name= MODEL_NAME)
# result = t.translate_segments(test_segments)

# print("\n✅ KẾT QUẢ DỊCH THUẬT:")
# for s in result:
#     print(f"🇬🇧 EN: {s.original_text}")
#     print(f"🇻🇳 VI: {s.translated_text}\n")






# # ======================================================
# # --- ĐANG TEST: AI MICROSOFT EDGE TTS (TẠO GIỌNG ĐỌC) ---
# # ======================================================
# print("\n--- TEST AI MICROSOFT EDGE TTS ---")

# from project import VoiceSynthesizer

# # Gọi nhạc trưởng của Bước 7
# vs = VoiceSynthesizer()

# # Lấy luôn kết quả (biến 'result') từ bước Dịch thuật ở ngay bên trên đưa vào đây
# tts_result = vs.synthesize(result)

# print("\n✅ TTS ĐÃ ĐỌC XONG! KẾT QUẢ:")
# for s in tts_result:
#     print(f"Câu: {s.translated_text}")
#     print(f"-> Đã lưu file mp3 tại: {s.audio_path}\n")





# # ======================================================
# # --- ĐANG TEST: BƯỚC 8 - MIX ÂM THANH (CÓ GIỮ GIỌNG GỐC) ---
# # ======================================================
# print("\n--- TEST AI PYDUB (AUDIO MIXING) ---")

# from project import AudioMixer
# import os
# from config import TEMP_DIR

# bgm_test_path = os.path.join(TEMP_DIR, "separated", "htdemucs", "test_audio", "no_vocals.wav")
# vocal_test_path = os.path.join(TEMP_DIR, "separated", "htdemucs", "test_audio", "vocals.wav")

# if not os.path.exists(bgm_test_path) or not os.path.exists(vocal_test_path):
#     print("⚠️ LỖI: Không tìm thấy file gốc của Demucs!")
# else:
#     mixer = AudioMixer()

#     # Truyền đủ 3 món: Giọng TTS, Nhạc nền, và Giọng gốc
#     final_audio = mixer.mix_dubbing_with_background(tts_result, bgm_test_path, vocal_test_path)
#     print("\n✅ ĐÃ MIX ÂM THANH THÀNH CÔNG!")
#     print(f"👉 Hãy bật nghe thử file này: {final_audio}\n")




import os 
import sys 
# Thêm đường dẫn để gọi project
file_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if file_ not in sys.path:
    sys.path.append(file_)

from project import DubbingApp, SetupManager
from config import OUTPUT_DIR

# ======================================================
# --- BẤM NÚT CHẠY TOÀN BỘ CỖ MÁY LỒNG TIẾNG ---
# ======================================================

print("\n" + "="*50)
print("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM TOÀN BỘ CỖ MÁY 🚀")
print("="*50)


# Tên mô hình bạn đang dùng
MODEL_NAME = "gemma4:e4b"

# Kiểm tra đảm bảo có model trước khi chạy
SetupManager.ensure_model_ready(MODEL_NAME)

# 1. Đường dẫn file (Đảm bảo bạn có file test_video_1.mp4 trong thư mục tests/test_videos)
input_vid = os.path.join(file_, "tests", "test_videos", "test_video_1.mp4")
output_vid = os.path.join(file_, "tests", "output", "final_dubbed_video.mp4")


if not os.path.exists(input_vid):
    print(f"\n⚠️ LỖI: Không tìm thấy video tại: {input_vid}")
    print("Mẹo: Hãy copy một đoạn video tiếng Anh ngắn (khoảng 10-30s) vào thư mục tests/test_videos/ và đổi tên thành 'test_video_1.mp4' nhé!")

else:
    # 2. Khởi tạo Nhạc trưởng
    app = DubbingApp(model_name=MODEL_NAME)
    # 3. Giao việc cho Nhạc trưởng
    app.process_video(input_vid, output_vid)