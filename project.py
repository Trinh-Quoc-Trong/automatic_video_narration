from edge_tts import communicate
import os
import sys
import webbrowser
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # fix OpenMP conflict

from dataclasses import dataclass
import subprocess
from typing import List
from moviepy import VideoFileClip, AudioFileClip
import re
from config import ROOT_DIR, TEMP_DIR, TEST_DIR, OUTPUT_DIR
import shutil


@dataclass
class SubtitleSegment():
    start_time: float
    end_time: float
    original_text: str
    translated_text: str = ""
    audio_path: str = ""


class MediaProcessor():
    """Extract audio from video and merge new audio back"""
    def extact_audio(self, video_path: str, output_audio_path: str) -> str:
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
        try:
            video = VideoFileClip(video_path)
            new_audio = AudioFileClip(new_audio_path)
            # MoviePy v2 changed set_audio -> with_audio
            if hasattr(video, "with_audio"):
                video_final = video.with_audio(new_audio)
            else:
                video_final = video.set_audio(new_audio)
            video_final.write_videofile(output_path, logger=None)
            video.close()
            new_audio.close()
            video_final.close()
        except Exception as e:
            raise RuntimeError(f"Error: {e}")


class SetupManager:
    """Check if Ollama + model are installed, guide user if not"""
    @staticmethod
    def ensure_model_ready(model_name: str):
        print("--- Checking system resources ---")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if model_name not in result.stdout:
                print(f"Model {model_name} not found. Downloading...")
                subprocess.run(["ollama", "pull", model_name], check=True)
                print(f"Done! {model_name} downloaded.")
            else:
                print(f"Model {model_name} ready.")

        except FileNotFoundError:
            print("\nOllama is not installed!")
            print("Opening download page...")
            webbrowser.open("https://ollama.com/download")
            raise RuntimeError(
                "\n--- SETUP GUIDE ---\n"
                "1. Download and install Ollama from the page that just opened.\n"
                "2. Close and reopen your terminal after installing.\n"
                "3. Run python project.py again.\n"
                "-------------------"
            )


def validate_video_file(path: str) -> bool:
    """Check if the video file is valid before processing"""
    valid_extensions = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
    if not os.path.isfile(path):
        raise ValueError(f"File does not exist: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in valid_extensions:
        raise ValueError(f"Unsupported format: {ext}")
    if os.path.getsize(path) == 0:
        raise ValueError("File is empty")
    return True


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    if seconds < 0:
        raise ValueError("Timestamp must not be negative")
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segment: list, output_path: str) -> str:
    """Write .srt subtitle file from a list of SubtitleSegments"""
    if not segment:
        raise ValueError("Segment list is empty")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segment, 1):
            start = format_timestamp(seg.start_time)
            end = format_timestamp(seg.end_time)
            # use translated text if available, otherwise keep original
            text = seg.translated_text if seg.translated_text else seg.original_text
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return output_path


class AudioSeparator():
    """Use Demucs to split vocals and background music"""
    def separate(self, audio_path: str) -> tuple[str, str]:
        out_dir = os.path.join(TEMP_DIR, "separated")
        try:
            # sys.executable so it uses the venv python, not system python
            subprocess.run(
                [sys.executable, "-m", "demucs", "--two-stems", "vocals", "-o", out_dir, audio_path],
                check=True,
                capture_output=True
            )
            filename = os.path.splitext(os.path.basename(audio_path))[0]
            vocal_path = os.path.join(TEMP_DIR, "separated", "htdemucs", filename, "vocals.wav")
            bgm_path = os.path.join(TEMP_DIR, "separated", "htdemucs", filename, "no_vocals.wav")

            if not os.path.isfile(vocal_path) or not os.path.isfile(bgm_path):
                raise FileNotFoundError("Demucs finished but output files are missing!")
            return vocal_path, bgm_path

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
            raise RuntimeError(f"Demucs error: {error_msg}")


class SpeechRecognizer():
    """Transcribe audio to text with timestamps using Whisper"""
    def transcribe(self, vocal_audio_path: str) -> List[SubtitleSegment]:
        from faster_whisper import WhisperModel  # heavy import, only load when needed

        model = WhisperModel("large-v3-turbo", device="auto", compute_type="float16")
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


class Translator():
    """Translate English text to Vietnamese using local Ollama model"""
    def __init__(self, model_name: str):
        self.model_name = model_name

    def translate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        print(f"  Translating {len(segments)} segments...")
        import ollama

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
            # some models wrap output in <think> tags, strip those out
            clean_text = re.sub(r"<think>.*?</think>", '', raw_text, flags=re.DOTALL).strip()
            seg.translated_text = clean_text

        return segments


class VoiceSynthesizer():
    """Generate Vietnamese speech using Edge TTS (free, no API key needed)"""
    def synthesize(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        print(f"  Generating TTS for {len(segments)} segments...")
        import edge_tts
        import asyncio

        audio_out_dir = os.path.join(TEMP_DIR, "tts_audio")
        os.makedirs(audio_out_dir, exist_ok=True)

        async def _generate_audio():
            for i, seg in enumerate(segments):
                text_to_read = seg.translated_text if seg.translated_text else seg.original_text
                audio_filepath = os.path.join(audio_out_dir, f"seg_{i}.mp3")
                try:
                    communicate = edge_tts.Communicate(
                        text=text_to_read,
                        voice="vi-VN-HoaiMyNeural",
                        rate="+10%"
                    )
                    await communicate.save(audio_filepath)
                    seg.audio_path = audio_filepath
                except Exception as e:
                    print(f"  TTS failed for segment {i}: {e}")
                    seg.audio_path = ""

        asyncio.run(_generate_audio())
        return segments


class AudioMixer():
    """Mix dubbed voice + background music + original voice"""
    def mix_dubbing_with_background(self, segments: List[SubtitleSegment], bgm_path: str, vocal_path: str) -> str:
        print("  Mixing audio tracks...")
        from pydub import AudioSegment

        bgm = AudioSegment.from_file(bgm_path)
        original_vocal = AudioSegment.from_file(vocal_path)

        # lower the volume so they don't overpower the dubbed voice
        bgm = bgm - 10
        original_vocal = original_vocal - 12

        base_track = bgm.overlay(original_vocal)
        dub_track = AudioSegment.silent(duration=len(base_track))

        for i, seg in enumerate(segments):
            if not seg.audio_path or not os.path.exists(seg.audio_path):
                continue
            voice = AudioSegment.from_file(seg.audio_path)
            insert_position_ms = int(seg.start_time * 1000)
            dub_track = dub_track.overlay(voice, position=insert_position_ms)

        final_mix = base_track.overlay(dub_track)
        output_path = os.path.join(TEMP_DIR, "final_dubbing_mix.wav")
        final_mix.export(output_path, format="wav")
        return output_path


class DubbingApp():
    """Main app - runs the full dubbing pipeline"""
    def __init__(self, model_name: str):
        self.media_processor = MediaProcessor()
        self.separator = AudioSeparator()
        self.recognizer = SpeechRecognizer()
        self.synthesizer = VoiceSynthesizer()
        self.mixer = AudioMixer()
        self.translator = Translator(model_name=model_name)

    def clean_temp_workspace(self):
        """Wipe temp folder to avoid leftover files from previous runs"""
        from config import TEMP_DIR
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        print("  Workspace cleaned.")

    def process_video(self, input_video_path: str, output_video_path: str):
        from config import TEMP_DIR

        print("\nStarting dubbing pipeline...")
        self.clean_temp_workspace()

        print("1. Extracting audio...")
        temp_audio = os.path.join(TEMP_DIR, "extracted_audio.wav")
        audio_path = self.media_processor.extact_audio(input_video_path, temp_audio)

        print("2. Separating vocals and background (Demucs)...")
        vocal_path, bgm_path = self.separator.separate(audio_path)

        print("3. Transcribing speech (Whisper)...")
        segments = self.recognizer.transcribe(vocal_path)

        print("4. Translating to Vietnamese...")
        segments = self.translator.translate_segments(segments)

        print("5. Generating subtitles (.srt)...")
        srt_output = os.path.splitext(output_video_path)[0] + ".srt"
        generate_srt(segments, srt_output)
        print(f"   Saved: {srt_output}")

        print("6. Generating Vietnamese voice (TTS)...")
        segments = self.synthesizer.synthesize(segments)

        print("7. Mixing audio...")
        final_audio_path = self.mixer.mix_dubbing_with_background(segments, bgm_path, vocal_path)

        print("8. Exporting final video...")
        self.media_processor.merge_audio_to_video(input_video_path, final_audio_path, output_video_path)

        self.clean_temp_workspace()
        print(f"\nDone! Output: {output_video_path}")


def main():
    MODEL_NAME = "gemma4:e4b"
    SetupManager.ensure_model_ready(MODEL_NAME)

    video_input = input("Enter video path: ").strip()
    validate_video_file(video_input)

    output_path = os.path.join(OUTPUT_DIR, "dubbed_output.mp4")
    app = DubbingApp(model_name=MODEL_NAME)
    app.process_video(video_input, output_path)


if __name__ == "__main__":
    main()
