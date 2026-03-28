Đây là bản hướng dẫn chi tiết từng bước, theo đúng quy trình mà các kỹ sư hàng đầu thực hiện: **viết từng module nhỏ -> test ngay -> tích hợp -> test lại toàn bộ**.

---

## NGUYÊN TẮC CỐT LÕI

Kỹ sư giỏi không bao giờ viết hết rồi mới test. Họ làm theo vòng lặp:

```
Viết 1 function -> Test function đó -> Fix bug -> Commit -> Tiếp function kế
```

Mỗi bước dưới đây đều theo vòng lặp này.

---

## BƯỚC 1: Nền tảng -- `requirements.txt` + fix bugs

**1.1** Tạo file `requirements.txt` ở thư mục gốc `project/`, nội dung:

```
moviepy
demucs
faster-whisper
edge-tts
pydub
ollama
pytest
```

**1.2** Cài đặt dependencies (trong venv):

```powershell
pip install -r requirements.txt
```

**1.3** Cập nhật `.gitignore` -- mở file `.gitignore`, sửa thành:

```
venv/
__pycache__/
*.mp3
*.mp4
*.wav
temp/
output/
separated/
```

**1.4** Fix 3 bug hiện có trong `project.py`:

Bug 1 -- dòng 2-3: import thừa không dùng:

```python
# XÓA 2 dòng này:
from logging import Logger
import select
```

Bug 2 -- dòng 28: nối string với Exception sẽ crash:

```python
# SỬA TỪ:
print("Error:" + e)
# THÀNH:
print(f"Error: {e}")
```

Bug 3 -- dòng 81: gọi `extact_audio` thiếu tham số `output_audio_path`:

```python
# SỬA TỪ:
audio_path = self.media_processor.extact_audio(input_video_path)
# THÀNH:
audio_path = "temp/extracted_audio.wav"
self.media_processor.extact_audio(input_video_path, audio_path)
```

**1.5** Thêm `return output_audio_path` vào cuối method `extact_audio` (trước `except`), để nó trả về đường dẫn file audio.

**1.6** Commit:

```powershell
git add .
git commit -m "Phase 0: add requirements.txt, fix bugs, update gitignore"
```

---

## BƯỚC 2: Viết 3 hàm top-level (yêu cầu CS50P)

Mở `project.py`, thêm **ngay trên dòng `@dataclass`** (trước tất cả class):

**2.1** Thêm import cần thiết ở đầu file:

```python
import os
import sys
```

**2.2** Viết hàm `validate_video_file`:

```python
def validate_video_file(path: str) -> bool:
    valid_extensions = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
    if not os.path.isfile(path):
        raise ValueError(f"File không tồn tại: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in valid_extensions:
        raise ValueError(f"Định dạng không hỗ trợ: {ext}")
    if os.path.getsize(path) == 0:
        raise ValueError("File rỗng")
    return True
```

**2.3** Viết hàm `format_timestamp`:

```python
def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("Thời gian không được âm")
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

**2.4** Viết hàm `generate_srt`:

```python
def generate_srt(segment: list, output_path: str) -> str:
    if not segment:
        raise ValueError("Danh sách segment rỗng")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segment, 1):
            start = format_timestamp(seg.start_time)
            end = format_timestamp(seg.end_time)
            text = seg.translated_text if seg.translated_text else seg.original_text
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return output_path
```

**2.5** Test ngay -- mở `test_project.py`, viết lại hoàn chỉnh:

```python
import pytest
import os
from project import validate_video_file, format_timestamp, generate_srt, SubtitleSegment


def test_format_timestamp():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(65.5) == "00:01:05,500"
    assert format_timestamp(3661.123) == "01:01:01,123"


def test_format_timestamp_negative():
    with pytest.raises(ValueError):
        format_timestamp(-1)


def test_validate_video_file_not_found():
    with pytest.raises(ValueError):
        validate_video_file("khong_ton_tai.mp4")


def test_validate_video_file_bad_extension(tmp_path):
    fake = tmp_path / "file.txt"
    fake.write_text("hello")
    with pytest.raises(ValueError):
        validate_video_file(str(fake))


def test_generate_srt(tmp_path):
    segments = [
        SubtitleSegment(0.0, 2.5, "Hello world", "Xin chào thế giới"),
        SubtitleSegment(3.0, 5.0, "Goodbye", "Tạm biệt"),
    ]
    output = tmp_path / "test.srt"
    result = generate_srt(segments, str(output))
    assert os.path.isfile(result)
    content = output.read_text(encoding="utf-8")
    assert "Xin chào thế giới" in content
    assert "00:00:00,000 --> 00:00:02,500" in content


def test_generate_srt_empty():
    with pytest.raises(ValueError):
        generate_srt([], "output.srt")
```

**2.6** Chạy test:

```powershell
pytest test_project.py -v
```

Nếu tất cả **PASSED** -> Commit:

```powershell
git add .
git commit -m "Phase 1: add 3 top-level functions with tests"
```

Nếu có test **FAILED** -> đọc lỗi, sửa code, chạy lại test cho đến khi pass hết.

---

## BƯỚC 3: Hoàn thiện MediaProcessor

**3.1** Sửa method `extact_audio` cho hoàn chỉnh:

```python
def extact_audio(self, video_path: str, output_audio_path: str) -> str:
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path, logger=None)
        audio.close()
        video.close()
        return output_audio_path
    except Exception as e:
        raise RuntimeError(f"Lỗi tách audio: {e}")
```

**3.2** Viết method `merge_audio_to_video`:

```python
def merge_audio_to_video(self, video_path: str, new_audio_path: str, output_path: str):
    try:
        from moviepy.editor import AudioFileClip
        video = VideoFileClip(video_path)
        new_audio = AudioFileClip(new_audio_path)
        final_video = video.set_audio(new_audio)
        final_video.write_videofile(output_path, logger=None)
        new_audio.close()
        video.close()
    except Exception as e:
        raise RuntimeError(f"Lỗi ghép audio vào video: {e}")
```

**3.3** Test thủ công: chuẩn bị 1 file video nhỏ (vd: `test.mp4`), mở Python terminal:

```python
from project import MediaProcessor
mp = MediaProcessor()
mp.extact_audio("test.mp4", "temp/test_audio.wav")
# Kiểm tra file temp/test_audio.wav có tồn tại và nghe được không
```

**3.4** Commit:

```powershell
git add .
git commit -m "Phase 2: complete MediaProcessor extract and merge"
```

---

## BƯỚC 4: Implement AudioSeparator (demucs)

**4.1** Tìm hiểu cách demucs hoạt động. Chạy thử trong terminal:

```powershell
python -m demucs --two-stems vocals temp/test_audio.wav
```

Lệnh này sẽ tạo thư mục `separated/htdemucs/test_audio/` chứa `vocals.wav` và `no_vocals.wav`. Hãy chạy thử và kiểm tra kết quả trước.

**4.2** Implement method `separate` trong class `AudioSeparator`:

```python
import subprocess

class AudioSeparator():
    """Tách vocal (giọng nói) và background music (nhạc nền)"""
    def separate(self, audio_path: str) -> tuple[str, str]:
        try:
            subprocess.run(
                ["python", "-m", "demucs", "--two-stems", "vocals", "-o", "temp/separated", audio_path],
                check=True,
                capture_output=True
            )
            filename = os.path.splitext(os.path.basename(audio_path))[0]
            vocal_path = f"temp/separated/htdemucs/{filename}/vocals.wav"
            bgm_path = f"temp/separated/htdemucs/{filename}/no_vocals.wav"

            if not os.path.isfile(vocal_path) or not os.path.isfile(bgm_path):
                raise FileNotFoundError("Demucs không tạo được file output")

            return vocal_path, bgm_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Lỗi tách audio: {e.stderr.decode()}")
```

**4.3** Test thủ công:

```python
from project import AudioSeparator
sep = AudioSeparator()
vocal, bgm = sep.separate("temp/test_audio.wav")
print(vocal, bgm)
# Nghe thử 2 file: vocal chỉ có giọng nói, bgm chỉ có nhạc nền
```

**4.4** Commit:

```powershell
git add .
git commit -m "Phase 3: implement AudioSeparator with demucs"
```

---

## BƯỚC 5: Implement SpeechRecognizer (faster-whisper)

**5.1** Implement method `transcribe`:

```python
class SpeechRecognizer():
    """Chuyển đổi âm thanh thành văn bản kèm thời gian (STT)"""
    def transcribe(self, vocal_audio_path: str) -> List[SubtitleSegment]:
        from faster_whisper import WhisperModel

        model = WhisperModel("large-v3", device="auto", compute_type="float16")
        segments_raw, info = model.transcribe(
            vocal_audio_path,
            beam_size=5,
            language="en",
            vad_filter=True
        )

        segments = []
        for seg in segments_raw:
            segments.append(SubtitleSegment(
                start_time=seg.start,
                end_time=seg.end,
                original_text=seg.text.strip()
            ))
        return segments
```

**Lưu ý quan trọng:** Lần đầu chạy, faster-whisper sẽ tải model `large-v3` (~3GB). Cần internet và kiên nhẫn đợi.

**5.2** Test thủ công:

```python
from project import SpeechRecognizer
rec = SpeechRecognizer()
segments = rec.transcribe("temp/separated/htdemucs/test_audio/vocals.wav")
for s in segments:
    print(f"[{s.start_time:.1f}s - {s.end_time:.1f}s] {s.original_text}")
```

Kiểm tra: text tiếng Anh có đúng không? Timestamp có hợp lý không?

**5.3** Commit:

```powershell
git add .
git commit -m "Phase 4: implement SpeechRecognizer with faster-whisper"
```

---

## BƯỚC 6: Implement Translator (Ollama)

**6.1** Đảm bảo Ollama đang chạy và đã pull model:

```powershell
ollama pull qwen2.5:7b
ollama list   # kiểm tra model có trong danh sách
```

**6.2** Implement method `translate_segments`:

```python
class Translator():
    """Dịch văn bản"""
    def translate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        import ollama

        for seg in segments:
            response = ollama.chat(model="qwen2.5:7b", messages=[
                {
                    "role": "system",
                    "content": "Bạn là một dịch giả chuyên nghiệp. Dịch câu tiếng Anh sang tiếng Việt tự nhiên. Chỉ trả về bản dịch, không giải thích."
                },
                {
                    "role": "user",
                    "content": seg.original_text
                }
            ])
            seg.translated_text = response["message"]["content"].strip()
        return segments
```

**6.3** Test thủ công:

```python
from project import Translator, SubtitleSegment
t = Translator()
test_segments = [
    SubtitleSegment(0, 2, "Hello, welcome to my channel"),
    SubtitleSegment(3, 5, "Today we will learn Python"),
]
result = t.translate_segments(test_segments)
for s in result:
    print(f"EN: {s.original_text}")
    print(f"VI: {s.translated_text}")
    print()
```

Kiểm tra: bản dịch có tự nhiên không?

**6.4** Commit:

```powershell
git add .
git commit -m "Phase 5: implement Translator with Ollama qwen2.5:7b"
```

---

## BƯỚC 7: Implement VoiceSynthesizer (edge-tts)

**7.1** Thử nghiệm edge-tts trước. Chạy trong terminal:

```powershell
edge-tts --voice vi-VN-HoaiMyNeural --text "Xin chào thế giới" --write-media test_tts.mp3
```

Nghe file `test_tts.mp3` -- nếu OK thì tiếp.

**7.2** Implement method `synthesize`:

```python
class VoiceSynthesizer():
    """Chuyển văn bản thành giọng nói (TTS)"""
    def synthesize(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        import asyncio
        import edge_tts

        os.makedirs("temp/tts", exist_ok=True)

        async def generate_audio(seg, index):
            output_path = f"temp/tts/segment_{index:04d}.mp3"
            communicate = edge_tts.Communicate(
                seg.translated_text,
                "vi-VN-HoaiMyNeural"
            )
            await communicate.save(output_path)
            seg.audio_path = output_path

        async def run_all():
            tasks = [generate_audio(seg, i) for i, seg in enumerate(segments)]
            await asyncio.gather(*tasks)

        asyncio.run(run_all())
        return segments
```

**7.3** Test thủ công:

```python
from project import VoiceSynthesizer, SubtitleSegment
vs = VoiceSynthesizer()
test_segs = [
    SubtitleSegment(0, 3, "Hello", "Xin chào các bạn", ""),
    SubtitleSegment(4, 7, "Goodbye", "Tạm biệt nhé", ""),
]
result = vs.synthesize(test_segs)
for s in result:
    print(f"{s.translated_text} -> {s.audio_path}")
# Nghe thử các file trong temp/tts/
```

**7.4** Commit:

```powershell
git add .
git commit -m "Phase 6: implement VoiceSynthesizer with edge-tts"
```

---

## BƯỚC 8: Implement AudioMixer (pydub)

**8.1** Implement method `mix_dubbing_with_background`:

```python
class AudioMixer():
    """Mix giọng đọc mới với nhạc nền cũ"""
    def mix_dubbing_with_background(self, segments: List[SubtitleSegment], bgm_path: str) -> str:
        from pydub import AudioSegment

        bgm = AudioSegment.from_file(bgm_path)
        bgm = bgm - 6  # giảm volume nhạc nền 6dB

        for seg in segments:
            if not seg.audio_path or not os.path.isfile(seg.audio_path):
                continue
            tts_audio = AudioSegment.from_file(seg.audio_path)
            position_ms = int(seg.start_time * 1000)
            bgm = bgm.overlay(tts_audio, position=position_ms)

        output_path = "temp/final_mixed_audio.wav"
        bgm.export(output_path, format="wav")
        return output_path
```

**8.2** Test thủ công (dùng output từ các bước trước):

```python
from project import AudioMixer, SubtitleSegment
mixer = AudioMixer()
segs = [
    SubtitleSegment(0, 3, "", "Xin chào", "temp/tts/segment_0000.mp3"),
    SubtitleSegment(4, 7, "", "Tạm biệt", "temp/tts/segment_0001.mp3"),
]
result = mixer.mix_dubbing_with_background(segs, "temp/separated/htdemucs/test_audio/no_vocals.wav")
print(result)
# Nghe file temp/final_mixed_audio.wav -- phải nghe được cả giọng Việt và nhạc nền
```

**8.3** Commit:

```powershell
git add .
git commit -m "Phase 7: implement AudioMixer with pydub"
```

---

## BƯỚC 9: Tích hợp DubbingApp + CLI

**9.1** Sửa `DubbingApp.process_video()` cho đúng (fix lời gọi hàm, thêm tạo thư mục temp):

```python
def process_video(self, input_video_path: str, output_video_path: str):
    os.makedirs("temp", exist_ok=True)

    print("1. Đang tách âm thanh...")
    audio_path = self.media_processor.extact_audio(input_video_path, "temp/full_audio.wav")

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
```

**9.2** Viết hàm `main()` với CLI:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto Video Dubbing: English to Vietnamese")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn video đầu vào")
    parser.add_argument("--output", "-o", default="output/dubbed_video.mp4", help="Đường dẫn video đầu ra")
    args = parser.parse_args()

    validate_video_file(args.input)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    app = DubbingApp()
    app.process_video(args.input, args.output)
```

**9.3** Test end-to-end -- đây là bước quan trọng nhất. Chuẩn bị 1 video tiếng Anh ngắn (~30 giây):

```powershell
python project.py --input test_video.mp4 --output output/result.mp4
```

Theo dõi 7 bước chạy tuần tự. Khi xong, mở `output/result.mp4` và kiểm tra:
- Video có giọng đọc tiếng Việt?
- Nhạc nền vẫn còn?
- Giọng đọc đúng thời điểm?

**9.4** Commit:

```powershell
git add .
git commit -m "Phase 8: integrate DubbingApp pipeline and CLI"
```

---

## BƯỚC 10: Hoàn thiện Tests

Quay lại `test_project.py`, đảm bảo có đủ test cho 3 hàm top-level (đã viết ở bước 2). Chạy lần cuối:

```powershell
pytest test_project.py -v
```

Tất cả phải **PASSED**. Nếu bước 2 bạn đã viết test đầy đủ và pass hết thì bước này chỉ cần xác nhận lại.

---

## BƯỚC 11: Viết README.md

Tạo file `README.md` với cấu trúc:

```markdown
# Auto Video Dubbing (English -> Vietnamese)

## Mô tả
Phần mềm lồng tiếng video tự động từ tiếng Anh sang tiếng Việt
sử dụng AI (Speech-to-Text, Translation, Text-to-Speech).

## Yêu cầu hệ thống
- Python 3.10+
- FFmpeg
- Ollama + model qwen2.5:7b

## Cài đặt
pip install -r requirements.txt
ollama pull qwen2.5:7b

## Cách sử dụng
python project.py --input video.mp4 --output output/dubbed.mp4

## Công nghệ
- faster-whisper (STT)
- demucs (Audio Separation)
- Ollama + qwen2.5:7b (Translation)
- edge-tts (TTS)
- MoviePy + pydub (Video/Audio Processing)
```

---

## BƯỚC 12: Kiểm tra cuối cùng & Nộp bài

Checklist cuối cùng trước khi nộp:

```
[ ] pytest test_project.py -v         -> tất cả PASSED
[ ] python project.py --input X --output Y  -> chạy end-to-end OK
[ ] requirements.txt                  -> có đủ dependencies
[ ] README.md                         -> mô tả rõ ràng
[ ] project.py có main() + 3 hàm top-level
[ ] test_project.py test được 3 hàm top-level
```

Commit cuối:

```powershell
git add .
git commit -m "Final: complete CS50P final project - Auto Video Dubbing"
```

---

## Tóm tắt thứ tự thực hiện

| Bước | Nội dung | File sửa |
|------|----------|----------|
| 1 | requirements.txt + fix bugs | requirements.txt, .gitignore, project.py |
| 2 | 3 hàm top-level + tests | project.py, test_project.py |
| 3 | MediaProcessor | project.py |
| 4 | AudioSeparator (demucs) | project.py |
| 5 | SpeechRecognizer (faster-whisper) | project.py |
| 6 | Translator (Ollama) | project.py |
| 7 | VoiceSynthesizer (edge-tts) | project.py |
| 8 | AudioMixer (pydub) | project.py |
| 9 | Tích hợp DubbingApp + CLI | project.py |
| 10 | Hoàn thiện tests | test_project.py |
| 11 | README.md | README.md |
| 12 | Kiểm tra cuối + nộp bài | -- |

---

Bạn sẵn sàng bắt đầu từ **Bước 1** chưa? Khi bạn làm, cứ nhắn kết quả (hoặc lỗi) cho tôi -- tôi sẽ hướng dẫn bạn xử lý từng tình huống.