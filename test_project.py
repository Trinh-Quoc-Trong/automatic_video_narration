import project 
import pytest
from unittest.mock import patch, MagicMock

# Test case 1: Đường truyền thành công (Happy Path)
def test_extact_audio_success() -> None:
    # Khởi tạo class cần test
    processor = project.MediaProcessor()
    