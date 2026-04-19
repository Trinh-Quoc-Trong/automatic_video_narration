# Automatic Video Dubbing - English to Vietnamese

#### Video Demo: <URL_HERE>

## Description

This is a command-line tool that takes an English video and produces a Vietnamese dubbed version. I built the whole thing to run locally — no cloud APIs, no paid subscriptions. You just need a video file and a decent GPU.

The idea is simple: extract audio from the video, transcribe the English speech, translate it to Vietnamese, generate a Vietnamese voice reading the translation, then mix everything back together. The result is a video where the speaker "talks" in Vietnamese while the original background music is preserved.

## Why I Made This

I don't speak English well. And I know a lot of Vietnamese people share the same struggle — there are amazing educational videos on YouTube (MIT, Stanford, CS50 itself) that are essentially locked behind a language wall. Subtitles help, but you can't really watch a video and read subtitles at the same time without losing something.

So I thought: what if the video just... spoke Vietnamese? That's what this project does.

## How It Works

The pipeline has 8 steps:

1. **Extract audio** from the input video (MoviePy)
2. **Separate vocals and background music** using Demucs (Meta's AI model)
3. **Transcribe** the English speech to text with timestamps (Faster Whisper)
4. **Translate** each sentence from English to Vietnamese (Gemma 4 via Ollama, running locally)
5. **Generate subtitles** — write a .srt file from the translated segments
6. **Text-to-speech** — generate Vietnamese audio for each sentence (Microsoft Edge TTS)
7. **Mix audio** — combine the dubbed voice, background music, and a quiet version of the original voice (pydub)
8. **Export** the final dubbed video (MoviePy)

## Project Structure

```
project/
├── project.py          # main code
├── test_project.py     # pytest tests
├── config.py           # path constants
├── requirements.txt
├── README.md
├── tests/
│   ├── test_manual.py  # step-by-step integration tests (used during development)
│   └── test_videos/
├── output/
└── temp/               # auto-cleaned between runs
```

## Functions

Besides `main()`, the project has 3 top-level functions:

- **`validate_video_file(path)`** — checks that the file exists, has a supported extension (.mp4, .avi, .mkv, .mov, .webm), and isn't empty
- **`format_timestamp(seconds)`** — converts float seconds to SRT format like `01:02:03,456`
- **`generate_srt(segments, output_path)`** — writes an .srt subtitle file from a list of SubtitleSegments

## Design Decisions

- Each step of the pipeline is its own class (MediaProcessor, AudioSeparator, SpeechRecognizer, etc.) and the `DubbingApp` class connects them all together. This made it much easier to test each piece individually during development.
- I used `sys.executable` instead of just `"python"` when calling Demucs as a subprocess, because I kept running into issues where it would use the system Python instead of my venv.
- Translation uses Gemma 4 running locally through Ollama. No API keys, no costs. The trade-off is you need a GPU with enough VRAM.
- For TTS I used `edge-tts` which piggybacks on Microsoft Edge's built-in Read Aloud feature. This avoids needing to sign up for Azure or any paid TTS service.
- The temp folder gets wiped before and after every run. I learned this the hard way — after a few test runs, I had 3GB of .wav files sitting there.

## Challenges I Ran Into

**FFmpeg/Windows conflict:** Demucs would finish 100% but then crash with `RuntimeError: Could not load libtorchcodec`. Turned out `torchaudio` on Windows has issues finding the FFmpeg DLL. I fixed it by installing `soundfile` as a fallback backend.

**Timestamp sync:** I was tempted to use regex to clean up the translated sentences (merge short ones, split long ones). But that would break the timestamps that Whisper carefully aligned. So instead I enforced a rule: the translation step can only change text, never touch the timestamps.

**AI giving bad output:** Sometimes Gemma returns empty strings or wraps its answer in `<think>` tags. I added a fallback — if the translation is empty, TTS just reads the original English instead of crashing.

## Testing

Run the unit tests:
```bash
pytest test_project.py -v
```

There are 7 tests covering `format_timestamp`, `validate_video_file`, and `generate_srt`. During development, I also tested each pipeline step individually — those manual tests are preserved (commented out) in `tests/test_manual.py`.

## How to Run

```bash
pip install -r requirements.txt
# install Ollama from https://ollama.com/download
python project.py
```

You'll need Python 3.10+, Ollama, and FFmpeg installed. A GPU is recommended for Whisper and Demucs but CPU works too (just slower).
