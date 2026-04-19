# Automatic Video Dubbing — English to Vietnamese

#### Video Demo: <URL_HERE>

## Table of Contents

- [Description](#description)
- [Motivation](#motivation)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Challenges & Lessons Learned](#challenges--lessons-learned)
- [Testing](#testing)
- [Installation & Usage](#installation--usage)
- [Requirements](#requirements)

## Description

**Automatic Video Dubbing** is a Python command-line application that takes an English-language video as input and produces a fully dubbed Vietnamese version — automatically. The entire pipeline runs locally on the user's machine, leveraging state-of-the-art AI models at every stage: speech recognition, machine translation, neural voice synthesis, and professional audio mixing. No cloud API keys or paid subscriptions are needed.

## Motivation

I don't speak English fluently. And I know I'm not the only one.

There are millions of incredible educational videos on YouTube — lectures from MIT, Stanford, Google — that are locked behind a language barrier. Vietnamese subtitles exist for some, but reading subtitles while trying to absorb complex technical content is exhausting. You end up either understanding the visuals or reading the text, but never both at the same time.

I built this project because I wanted to *hear* those videos in my own language. Not through robotic Google Translate, but through a natural-sounding Vietnamese voice, mixed properly with the original background music, so the experience feels like the video was made for Vietnamese speakers from the start.

This is my attempt to break that barrier — not just for me, but for anyone who has ever closed a YouTube tab because they couldn't understand the language.

## How It Works

The application executes a **7-step pipeline**, where each step feeds its output into the next:

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐
│  Input Video │───▶│ Extract Audio│───▶│ Separate Vocal│───▶│    STT     │
│   (.mp4)     │    │  (MoviePy)   │    │  & BGM (Demucs│    │ (Whisper)  │
└─────────────┘    └──────────────┘    └───────────────┘    └─────┬──────┘
                                                                  │
                   ┌──────────────┐    ┌───────────────┐    ┌─────▼──────┐
                   │ Output Video │◀───│  Mix Audio    │◀───│  Translate │
                   │   (.mp4)     │    │   (pydub)     │    │  (Gemma 4) │
                   └──────────────┘    └───────┬───────┘    └─────┬──────┘
                                               │                  │
                                               │            ┌─────▼──────┐
                                               │◀───────────│    TTS     │
                                                            │ (Edge TTS) │
                                                            └────────────┘
```

1. **Extract Audio** — Uses MoviePy to separate the audio track from the input video.
2. **Separate Vocals & Background Music** — Uses [Demucs](https://github.com/facebookresearch/demucs) (by Meta Research) to isolate the human voice from background music and sound effects.
3. **Speech-to-Text** — Uses [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) (a CTranslate2-optimized version of OpenAI's Whisper `large-v3-turbo`) to transcribe the English speech into text with precise timestamps.
4. **Translation** — Uses [Gemma 4](https://ollama.com/library/gemma4) running locally via [Ollama](https://ollama.com/) to translate each subtitle segment from English to natural Vietnamese. A regex filter strips any internal `<think>` reasoning tags from the model's output.
5. **Text-to-Speech** — Uses [Microsoft Edge Neural TTS](https://github.com/rany2/edge-tts) with the `vi-VN-HoaiMyNeural` voice to generate Vietnamese audio for each translated segment.
6. **Audio Mixing** — Uses [pydub](https://github.com/jiaaro/pydub) to mix three audio layers: the new Vietnamese voice-over, the original background music (reduced by 10 dB), and the original voice at a low volume (reduced by 12 dB) for a natural, professional result.
7. **Merge Back to Video** — Uses MoviePy to replace the original audio track with the final mixed audio, producing the dubbed output video.

## Project Structure

```
project/
├── project.py          # Main application (all classes and functions)
├── test_project.py     # Pytest unit tests
├── config.py           # Path configuration (ROOT_DIR, TEMP_DIR, etc.)
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── tests/              # Manual integration tests and test videos
│   ├── test_manual.py
│   └── test_videos/
├── output/             # Generated dubbed videos
└── temp/               # Temporary files (auto-cleaned)
```

## Design Decisions

- **Modular Architecture**: Each processing step is encapsulated in its own class (`MediaProcessor`, `AudioSeparator`, `SpeechRecognizer`, `Translator`, `VoiceSynthesizer`, `AudioMixer`), making the code easy to test, extend, and maintain. The `DubbingApp` class acts as a "conductor" that orchestrates the full pipeline.
- **Local AI Models**: Translation uses Gemma 4 via Ollama, running entirely on the user's machine — no API keys or cloud costs required.
- **Automatic Setup**: The `SetupManager` class detects whether Ollama is installed and whether the required model has been downloaded. If not, it provides clear instructions and even opens the download page in the user's browser automatically.
- **Workspace Cleanup**: The `DubbingApp` automatically cleans all temporary files before and after each run to prevent disk bloat and stale data from previous runs interfering with new ones.

## Challenges & Lessons Learned

Building this project was far from smooth. Here are the hardest problems I ran into and what I learned from each one:

### 1. FFmpeg & Windows Environment Conflicts

When Demucs finished separating audio at 100%, the system suddenly crashed with `RuntimeError: Could not load libtorchcodec`. The root cause was that `torchaudio` on Windows conflicts when searching for FFmpeg shared DLLs to save `.wav` files. Even worse, the subprocess call was silently using the system-wide Python instead of my virtual environment's Python.

**Fix:** I forced the subprocess to use `sys.executable` (which always points to the current venv's Python), and installed `soundfile` as a fallback audio backend to bypass the `torchcodec` issue entirely.

**Lesson:** Never assume `python` in a subprocess points to the right interpreter. Always use `sys.executable`.

### 2. Timestamp Synchronization — The Temptation of Regex

After Whisper transcribed the audio, I was tempted to use regex to split or merge subtitle text for "cleaner" sentences. But doing so would have destroyed the carefully aligned `start_time` and `end_time` values, causing the dubbed audio to fall completely out of sync with the video.

**Fix:** I applied a strict "Pipeline" principle — the `SubtitleSegment` data structure is locked from start to finish. Translation and TTS steps can only change the *text content*, never the *timestamps*.

**Lesson:** In a pipeline, protect your shared data structure like a contract. If one step breaks the contract, every downstream step breaks too.

### 3. Defensive Programming Against AI Imperfection

Gemma 4 is not perfect. Sometimes it fails to translate, returns an empty string, or includes internal reasoning tags (`<think>...</think>`) in the output. Feeding an empty string to TTS would crash the system or create dead silence in the video.

**Fix:** I applied a fallback mechanism using a ternary expression: `text_to_read = seg.translated_text if seg.translated_text else seg.original_text`. If there's no Vietnamese translation, the system automatically falls back to reading the original English text, ensuring the video always plays smoothly.

**Lesson:** Never trust external AI output blindly. Always have a fallback plan.

### 4. Disk Bloat — Gigabytes of Temporary Audio Files

Each run generates large `.wav` files (vocals, background, TTS segments). After several test runs, my `temp/` folder ballooned to multiple gigabytes without warning.

**Fix:** I designed an "Ephemeral Workspace" pattern — the `clean_temp_workspace()` function uses `shutil.rmtree()` to wipe the entire temp directory before starting and immediately after successfully exporting the video.

**Lesson:** Intermediate data is toxic if left unchecked. Clean up aggressively, especially with large binary files.

### 5. API Keys & Security — The Free TTS Trick

Getting natural-sounding AI voices normally requires paid cloud APIs (like Microsoft Azure TTS), which means embedding API keys in code — a security risk when pushing to GitHub.

**Fix:** I used the `edge-tts` library, which reverse-engineers the free "Read Aloud" feature built into Microsoft Edge. This gives the project access to high-quality neural voices (`vi-VN-HoaiMyNeural`) without any API key, any account, or any cost. The TTS calls run asynchronously with `asyncio` to avoid blocking the main thread.

**Lesson:** Before paying for an API, check if the same capability is already available for free through browser-native features.

## Testing

The project uses two layers of testing:

### Unit Tests (`test_project.py`)

Seven automated tests cover the three top-level utility functions, run with `pytest`:

| Test | What It Verifies |
|---|---|
| `test_format_timestamp` | Correct conversion of seconds to SRT format (0s, 65s, 65.5s, 3690.4s, edge cases) |
| `test_format_timestamp_negative` | Raises `ValueError` for negative timestamps |
| `test_validate_video_file` | Accepts valid `.avi` files, rejects `.txt` files, rejects non-existent files |
| `test_validate_video_file_empty` | Raises `ValueError` for 0-byte video files |
| `test_generate_srt_success` | Generates correct SRT content with translated text |
| `test_generate_srt_lack_translated_text` | Falls back to original English text when translation is empty |
| `test_generate_srt_lack_end_time` | Raises `ValueError` when segment list is empty |

Run the tests:
```bash
pytest test_project.py -v
```

### Manual Integration Tests (`tests/test_manual.py`)

During development, I tested each pipeline step individually — from audio extraction to Demucs separation to Whisper transcription to Ollama translation to TTS generation to audio mixing — before wiring them all together into the final `DubbingApp.process_video()` call. These step-by-step tests (now commented out) are preserved in `tests/test_manual.py` as documentation of the development process.

## Functions

The project contains a `main` function and three additional top-level functions:

- `validate_video_file(path)` — Validates that the input file exists, has a supported extension (`.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`), and is not empty.
- `format_timestamp(seconds)` — Converts a float (seconds) into SRT subtitle format (`HH:MM:SS,mmm`).
- `generate_srt(segments, output_path)` — Generates a `.srt` subtitle file from a list of `SubtitleSegment` objects.

## Installation & Usage

```bash
# 1. Clone the project and navigate to it
cd project

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate    # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Ollama from https://ollama.com/download
#    (The program will guide you automatically if it's missing)

# 5. Run the application
python project.py

# 6. Run tests
pytest test_project.py -v
```

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running
- FFmpeg (required by MoviePy and Demucs)
- A GPU is recommended for Whisper and Demucs (CPU fallback is supported)
