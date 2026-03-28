from io import text_encoding
import project 
import pytest
from unittest.mock import patch, MagicMock
import os

# Test case 1: test hàm format_timestamp 
def test_format_timestamp():
    # 0 giây phải ra 00:00:00,000
    assert project.format_timestamp(0) == "00:00:00,000"
    assert project.format_timestamp(65) == "00:01:05,000"
    assert project.format_timestamp(65.5) == "00:01:05,500"
    assert project.format_timestamp(3690.4) == "01:01:30,400"
    assert project.format_timestamp(36000000000.4) == "10000000:00:00,400"


def test_format_timestamp_negative():
    # test khi thời gian bị âm
    with pytest.raises(ValueError):
        project.format_timestamp(-1)
    with pytest.raises(ValueError):
        project.format_timestamp(-90000000000000)

def test_validate_video_file(tmp_path):
    # test chuyen file vao
    fake_file = tmp_path / "fake.avi"
    fake_file.write_text("trong dep trai")
    assert project.validate_video_file(fake_file) == True
    
    
    fake_file = tmp_path / "fake.txt"
    fake_file.write_text("trong dep trai")
    
    with pytest.raises(ValueError):
        project.validate_video_file(fake_file)
        
        
    fake_file_none = tmp_path / "fake.mp4" 
    
    with pytest.raises(ValueError):
        project.validate_video_file(fake_file_none)

        
def test_generate_srt_success(tmp_path):
    # 1. Định nghĩa đường dẫn file srt sẽ được lưu trong thư mục tạm
    output_file = tmp_path / "test.srt"

    fake_segments = [
        project.SubtitleSegment(
          start_time= 1.5,
          end_time=3.5,
          original_text="hello world",  
          translated_text="xin chào thế giới",
          audio_path=""
        ),
        
    ]
    # 3. Gọi hàm thực thi
    result = project.generate_srt(fake_segments, str(output_file))

    # 4. Kiểm chứng (Assert)
    assert os.path.isfile(result)
    
    
    text_encoding = ""
    with open(result, 'r', encoding= "utf-8") as f:
        text_encoding = f.read()
    
    assert text_encoding == f"1\n00:00:01,500 --> 00:00:03,500\nxin chào thế giới\n\n"

def test_generate_srt_lack_translated_text(tmp_path):
    """
    kiểm tra xem thiếu thuộc tính thì chuyện gì xẩy ra 
    """
    # 1. Định nghĩa đường dẫn file srt sẽ được lưu trong thư mục tạm
    output_file = tmp_path / "test.srt"

    fake_segments = [
        project.SubtitleSegment(
          start_time= 1.5,
          end_time=3.5,
          original_text="hello world",  
          translated_text="",
          audio_path=""
        ),
        
    ]
    # 3. Gọi hàm thực thi
    result = project.generate_srt(fake_segments, str(output_file))

    # 4. Kiểm chứng (Assert)
    assert os.path.isfile(result)
    
    
    with open(result, 'r', encoding= "utf-8") as f:
        context = f.read()
    
    
    assert context == "1\n00:00:01,500 --> 00:00:03,500\nhello world\n\n"




def test_generate_srt_lack_end_time(tmp_path):
    """
    kiểm tra xem thiếu thuộc tính thì chuyện gì xẩy ra 
    """
    # 1. Định nghĩa đường dẫn file srt sẽ được lưu trong thư mục tạm
    output_file = tmp_path / "test.srt"

    fake_segments = [
 
    ]

    with pytest.raises(ValueError):
        project.generate_srt(fake_segments, str(output_file))


# pytest test_project.py -v