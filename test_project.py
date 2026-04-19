import project
import pytest
import os


def test_format_timestamp():
    assert project.format_timestamp(0) == "00:00:00,000"
    assert project.format_timestamp(65) == "00:01:05,000"
    assert project.format_timestamp(65.5) == "00:01:05,500"
    assert project.format_timestamp(3690.4) == "01:01:30,400"
    assert project.format_timestamp(36000000000.4) == "10000000:00:00,400"


def test_format_timestamp_negative():
    with pytest.raises(ValueError):
        project.format_timestamp(-1)
    with pytest.raises(ValueError):
        project.format_timestamp(-90000000000000)


def test_validate_video_file(tmp_path):
    # valid file
    fake_file = tmp_path / "fake.avi"
    fake_file.write_text("test content")
    assert project.validate_video_file(fake_file) == True

    # wrong extension
    fake_file = tmp_path / "fake.txt"
    fake_file.write_text("test content")
    with pytest.raises(ValueError):
        project.validate_video_file(fake_file)

    # file doesn't exist
    fake_file_none = tmp_path / "fake.mp4"
    with pytest.raises(ValueError):
        project.validate_video_file(fake_file_none)


def test_validate_video_file_empty(tmp_path):
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError):
        project.validate_video_file(str(empty_file))


def test_generate_srt_success(tmp_path):
    output_file = tmp_path / "test.srt"
    fake_segments = [
        project.SubtitleSegment(
            start_time=1.5,
            end_time=3.5,
            original_text="hello world",
            translated_text="xin chào thế giới",
            audio_path=""
        ),
    ]
    result = project.generate_srt(fake_segments, str(output_file))
    assert os.path.isfile(result)

    with open(result, 'r', encoding="utf-8") as f:
        content = f.read()
    assert content == "1\n00:00:01,500 --> 00:00:03,500\nxin chào thế giới\n\n"


def test_generate_srt_lack_translated_text(tmp_path):
    """When translated_text is empty, should fall back to original_text"""
    output_file = tmp_path / "test.srt"
    fake_segments = [
        project.SubtitleSegment(
            start_time=1.5,
            end_time=3.5,
            original_text="hello world",
            translated_text="",
            audio_path=""
        ),
    ]
    result = project.generate_srt(fake_segments, str(output_file))
    assert os.path.isfile(result)

    with open(result, 'r', encoding="utf-8") as f:
        content = f.read()
    assert content == "1\n00:00:01,500 --> 00:00:03,500\nhello world\n\n"


def test_generate_srt_lack_end_time(tmp_path):
    """Empty segment list should raise ValueError"""
    output_file = tmp_path / "test.srt"
    with pytest.raises(ValueError):
        project.generate_srt([], str(output_file))