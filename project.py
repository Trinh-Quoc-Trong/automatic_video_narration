from dataclasses import dataclass
from multiprocessing.sharedctypes import Value
from typing import List
from moviepy.editor import VideoFileClip # dùng để cắt ghép video
import os
import sys


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
            audio.write_audiofile(output_audio_path, Logger=None)
            audio.close()
            video.close()
        except Exception as e:
            print(f"Error: {e}")
    
    def merge_audio_to_video(self, video_path: str, new_audio_path: str, output_path: str):
        # TODO: Ghép audio hoàn chỉnh vào video
        pass



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
    if second < 0:
        raise ValueError("Thời gian không được âm")
    hours = int(seconds // 3600)                # 65.5 // 3600 = 0 (giờ)
    minutes = int((seconds // 3600) // 60)      # 65.5 % 3600 = 65.5, 65.5 // 60 = 1 (phút)
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
            text = seg.translated_text if seg.translated else seg.original_text  #      ưu tiên text đã dịch, nếu chưa dịch thì dùng text gốc
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return output_path


    


class AudioSeparator():
    """Tách vocal (giọng nói) và background music (nhạc nền)"""
    def separate(self, audio_path: str) -> tuple[str, str]:
        # TODO: Trả về (vocal_path, background_music_path)
        pass


class SpeechRecognizer():
    """Chuyển đổi âm thanh thành văn bản kèm thời gian (STT)"""
    def transcribe(self, vocal_audio_path: str) -> List[SubtitleSegment]:
        pass


class Translator():
    """Dịch văn bản"""
    def translate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        # TODO: Gọi API dịch (Google/DeepL/OpenAI)
        pass


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
    def __init__(self):
        # Khởi tạo các module (Dependency Injection)
        self.media_processor = MediaProcessor()
        self.separator = AudioSeparator()
        self.recognizer = SpeechRecognizer()
        self.translator = Translator()
        self.synthesizer = VoiceSynthesizer()
        self.mixer = AudioMixer()
    
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
    app = DubbingApp()

if __name__ == "__main__":
    main()