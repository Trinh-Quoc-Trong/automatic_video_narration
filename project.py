import os
import sys
import webbrowser
# THÊM DÒNG NÀY VÀO ĐỂ SỬA LỖI ĐỤNG ĐỘ OPENMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dataclasses import dataclass
from multiprocessing.sharedctypes import Value
import subprocess
from typing import List
from moviepy import VideoFileClip, AudioFileClip  # MoviePy v2 API
import re
from numpy import divide
from config import  ROOT_DIR, TEMP_DIR, TEST_DIR, OUTPUT_DIR


#  --- DATA CLASSES ---
@dataclass
class SubtitleSegment():
    start_time: float
    end_time: float
    original_text: str
    translated_text: str = ""
    audio_path: str = ""
    
# --- SERVICE CLASSES ---
class MediaProcessor():
    """Xử lý việc tách âm thanh từ video và ghép âm thanh vào video"""
    def extact_audio(self, video_path: str, output_audio_path: str) -> str:
        # TODO: Dùng FFmpeg/MoviePy tách audio
        try:
            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(output_audio_path, logger=None)
            audio.close()
            video.close()
        except Exception as e:
            raise RuntimeError(f"Error: {e}")
        
        return output_audio_path
    
    def merge_audio_to_video(self, video_path: str, new_audio_path: str, output_path: str):
        # TODO: Ghép audio hoàn chỉnh vào video
        try: 
            video = VideoFileClip(video_path)
            new_audio = AudioFileClip(new_audio_path)
            if hasattr(video, "with_audio"):
                video_final = video.with_audio(new_audio)  # MoviePy v2
            else:
                video_final = video.set_audio(new_audio)   # MoviePy v1
            video_final.write_videofile(output_path, logger=None)
            video.close()
            new_audio.close()
            video_final.close()
            
        except Exception as e:
            raise RuntimeError(f"Error: {e}")
            

class SetupManager:
    """Tự động kiểm tra và thiết lập môi trường cho người dùng mới"""
    @staticmethod
    def ensure_model_ready(model_name: str):
        print(f"--- Đang kiểm tra tài nguyên hệ thống ---")
        try:
            # Kiểm tra danh sách model hiện có trong Ollama
            result = subprocess.run(["ollama","list"], capture_output = True, text = True)
            
            if model_name not in result.stdout:
                print(f"⚠️ Không tìm thấy {model_name}. Đang tự động tải về (lần đầu)...")
                subprocess.run(["ollama", 'pull', model_name], check=True)
                print(f"✅ Tải thành công {model_name}!")
            else:
                print(f"✅ Model {model_name} đã sẵn sàng.")
                
                
        except FileNotFoundError:
            print("\n❌ HỆ THỐNG THIẾU PHẦN MỀM LÕI!")
            print("Máy tính của bạn chưa được cài đặt Ollama.")
            print("Đang tự động mở trình duyệt để bạn tải về...")
            # Tự động bật Chrome/Edge truy cập thẳng vào trang tải Ollama
            webbrowser.open("https://ollama.com/download")          
            raise RuntimeError(
                "\n--- HƯỚNG DẪN CÀI ĐẶT ---\n"
                "1. Hãy tải và cài đặt Ollama từ trang web vừa mở.\n"
                "2. QUAN TRỌNG: Cài xong, hãy TẮT và MỞ LẠI VS Code (hoặc Terminal) này.\n"
                "3. Chạy lại lệnh python project.py để tiếp tục.\n"
                "---------------------------"
                )



def validate_video_file(path: str) -> bool:
    """
    CHỨC NĂNG: Kiểm tra file video đầu vào có hợp lệ không
    DÙNG KHI: Gọi trong main() TRƯỚC KHI chạy pipeline, để chặn lỗi sớm
    """
    valid_extensions = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
    if not os.path.isfile(path):
        raise ValueError(f"File không tồn tại: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in valid_extensions:
        raise ValueError(f"Định dạng file không hổi trợ: {ext}")
    if os.path.getsize(path) == 0:
        raise ValueError("file rỗng")
    return True


def format_timestamp(seconds: float) -> str:
    """
    CHỨC NĂNG: Chuyển số giây (float) thành định dạng phụ đề SRT
    DÙNG KHI: Tạo file phụ đề .srt (được gọi bởi hàm generate_srt)
    """
    if seconds < 0:
        raise ValueError("Thời gian không được âm")
    hours = int(seconds // 3600)                # 65.5 // 3600 = 0 (giờ)
    minutes = int((seconds % 3600) // 60)      # 65.5 % 3600 = 65.5, 65.5 // 60 = 1 (phút)
    secs = int(seconds % 60)                    # 65.5 % 60 = 5 (giây)
    millis = int(round((seconds % 1) * 1000))   # 0.5 * 1000 = 500 (mili-giây)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segment: list, output_path: str) -> str:
    """
    CHỨC NĂNG: Tạo file phụ đề .srt từ danh sách SubtitleSegment
    DÙNG KHI: Sau khi dịch xong, xuất file phụ đề để người dùng xem
    """
    if not segment:
        raise ValueError("Danh sách segments rỗng")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segment, 1):
            start = format_timestamp(seg.start_time)
            end = format_timestamp(seg.end_time)
            text = seg.translated_text if seg.translated_text else seg.original_text  #      ưu tiên text đã dịch, nếu chưa dịch thì dùng text gốc
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return output_path

    
    


class AudioSeparator():
    """Tách vocal (giọng nói) và background music (nhạc nền)"""
    def separate(self, audio_path: str) -> tuple[str, str]:
        # TODO: Trả về (vocal_path, background_music_path)
        out_dir = os.path.join(TEMP_DIR, "separated")
        try: 
            # Dùng thư viện subprocess để "bấm nốt" chạy lệnh terminal y hệt như bạn vừa gõ tay
            subprocess.run(
                ["python", "-m", "demucs", "--two-stems", "vocals", "-o", out_dir, audio_path],
            )
            
            # Lấy tên file gốc (ví dụ: "test_audio.wav" -> "test_audio")
            filename = os.path.splitext(os.path.basename(audio_path))[0]
            
            # Khớp đúng với đường dẫn mà Demucs tự động tạo ra
            vocal_path = os.path.join(TEMP_DIR, "separated", "htdemucs", filename, "vocals.wav")
            bgm_path = os.path.join(TEMP_DIR, "separated", "htdemucs", filename, "no_vocals.wav")
            
            if not os.path.isfile(vocal_path) or not os.path.isfile(bgm_path):
                raise FileNotFoundError("Demucs chạy xong nhưng không tìm thấy file output!")

            return vocal_path, bgm_path
        
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode("utf-8", errors = "ignore")
            raise RuntimeError(f"Lỗi tạch audio(Demucs): {error_msg}")


class SpeechRecognizer():
    """Chuyển đổi âm thanh thành văn bản kèm thời gian (STT)"""
    def transcribe(self, vocal_audio_path: str) -> List[SubtitleSegment]:
        # Import cục bộ để tránh ngốn RAM khi chưa dùng đến
        from faster_whisper import WhisperModel

        model = WhisperModel("large-v3-turbo", device = "auto", compute_type = "float16")
        
        segments_raw, info = model.transcribe(
            vocal_audio_path,
            beam_size=5,
            language="en",  # Ép AI hiểu đây là tiếng Anh để dịch chuẩn xác hơn
            vad_filter=True # Tính năng lọc khoảng lặng
        )
        
        segments = []
        for seg in segments_raw:
            # Đóng gói từng câu AI nghe được vào "khuôn" SubtitleSegment
            segments.append(SubtitleSegment(
                start_time=seg.start,
                end_time= seg.end,
                original_text= seg.text.strip()
            ))
        
        return segments

class Translator():
    """Dịch văn bản"""
    def __init__(self, model_name : str):
        self.model_name = model_name 

    def translate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        # TODO: Dịch văn bản bằng Gemma 4 (Local)
        print(f"  [AI] Đang nhờ Gemma 4 (e4b) dịch {len(segments)} câu sang tiếng Việt...")
        import ollama # Import nội bộ để tiết kiệm RAM khi khởi động
        
        for seg in segments:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    "role": "system",
                    "content": "Bạn là một dịch giả chuyên nghiệp. Dịch câu tiếng Anh sang tiếng Việt tự nhiên. Chỉ trả về bản dịch, tuyệt đối không giải thích."
                },
                {
                    "role": "user",
                    "content": seg.original_text
                }
            ])
            
            raw_text = response["message"]["content"].strip()

            # Lọc bỏ nội dung suy nghĩ <think>...</think> để tránh đưa vào video
            clean_text = re.sub(r"<think>.*?</think>", '', raw_text, flags=re.DOTALL).strip()
            
            seg.translated_text = clean_text
        
        return segments
        


class VoiceSynthesizer():
    """Chuyển văn bản thành giọng nói (TTS)"""
    def synthesize(self, segment: List[SubtitleSegment]) -> List[SubtitleSegment]:
        # TODO: Gọi API tạo giọng đọc tiếng Việt và lưu file audio cho từng segment
        pass


class AudioMixer():
    """Mix giọng đọc mới với nhạc nền cũ"""
    def mix_dubbing_with_background(self, segment: List[SubtitleSegment], bgm_path: str) -> str:
        pass


class DubbingApp():
    """Nhạc trưởng điều phối toàn bộ hệ thống"""
    def __init__(self, model_name : str):
        # Khởi tạo các module (Dependency Injection)
        self.media_processor = MediaProcessor()
        self.separator = AudioSeparator()
        self.recognizer = SpeechRecognizer()
        self.translator = Translator()
        self.synthesizer = VoiceSynthesizer()
        self.mixer = AudioMixer()

        self.translator = Translator(model_name = model_name)
    
    def process_video(self, input_video_path: str, output_video_path: str):
        print("1. Đang tách âm thanh...")
        audio_path = self.media_processor.extact_audio(input_video_path)
        
        
        print("2. Đang tách giọng nói và nhạc nền...")
        vocal_path, bgm_path = self.separator.separate(audio_path)

        print("3. Đang nhận diện giọng nói (STT)...")
        segments = self.recognizer.transcribe(vocal_path)
        
        print("4. Đang dịch thuật sang tiếng Việt...")
        segments = self.translator.translate_segments(segments)
        
        print("5. Đang tạo giọng đọc tiếng Việt (TTS)...")
        segments = self.synthesizer.synthesize(segments)
        
        print("6. Đang mix âm thanh lồng tiếng với nhạc nền...")
        final_audio_path = self.mixer.mix_dubbing_with_background(segments, bgm_path)
        
        print("7. Đang xuất video hoàn chỉnh...")
        self.media_processor.merge_audio_to_video(input_video_path, final_audio_path, output_video_path)
        
        print("Hoàn thành!")









def main():
    # Định nghĩa tên model chính xác
    MODEL_NAME = "gemma4:e4b"
    
    # Tự động chuẩn bị "não" AI
    SetupManager.ensure_model_ready(MODEL_NAME)
    
    # Khởi động ứng dụng
    app = DubbingApp(model_name= MODEL_NAME)

if __name__ == "__main__":
    main()
