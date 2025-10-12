"""
Unit tests for video processing functionality
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json
from datetime import datetime

# Import core modules directly to avoid dependency issues
import sys
sys.path.insert(0, '/Users/a/Desktop/Go2Rep')

from go2rep.core.processing.classifier import VideoClassifier
from go2rep.core.processing.encoder import VideoEncoder, EncoderBackend


class TestVideoClassifier:
    """Test VideoClassifier functionality"""
    
    def test_init(self):
        """Test initialization"""
        classifier = VideoClassifier()
        assert classifier.time_tolerance == 8
        
        classifier = VideoClassifier(time_tolerance=15)
        assert classifier.time_tolerance == 15
    
    def test_parse_timestamp_gopro_format(self):
        """Test parsing GoPro format timestamps"""
        classifier = VideoClassifier()
        
        # Valid GoPro format
        timestamp = classifier.parse_timestamp("20231201_120000-GoPro1234-test.mp4")
        assert timestamp == datetime(2023, 12, 1, 12, 0, 0)
        
        # Invalid format
        timestamp = classifier.parse_timestamp("invalid_filename.mp4")
        assert timestamp is None
        
        # Wrong convention
        timestamp = classifier.parse_timestamp("20231201_120000-GoPro1234-test.mp4", filename_convention=2)
        assert timestamp is None
    
    def test_parse_timestamp_camera_format(self):
        """Test parsing CAMERA format timestamps"""
        classifier = VideoClassifier()
        
        # Valid CAMERA format
        timestamp = classifier.parse_timestamp("20231201_120000-CAMERA1234-test.mp4", filename_convention=2)
        assert timestamp == datetime(2023, 12, 1, 12, 0, 0)
        
        # Invalid format
        timestamp = classifier.parse_timestamp("invalid_filename.mp4", filename_convention=2)
        assert timestamp is None
    
    def test_group_videos_by_trial(self):
        """Test grouping videos by trial"""
        classifier = VideoClassifier(time_tolerance=5)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test video files
            video1 = temp_path / "20231201_120000-GoPro1234-test.mp4"
            video2 = temp_path / "20231201_120003-GoPro5678-test.mp4"  # 3 seconds later
            video3 = temp_path / "20231201_120010-GoPro9012-test.mp4"  # 10 seconds later (new trial)
            video4 = temp_path / "invalid_format.mp4"  # Invalid format
            
            video1.touch()
            video2.touch()
            video3.touch()
            video4.touch()
            
            trials = classifier.group_videos_by_trial([video1, video2, video3, video4])
            
            # Should have 2 trials (first two videos together, third separate)
            assert len(trials) == 2
            assert len(trials[0]) == 2  # First trial has 2 videos
            assert len(trials[1]) == 1  # Second trial has 1 video
            
            # Check that videos are sorted by timestamp
            assert trials[0][0][0] == video1
            assert trials[0][1][0] == video2
            assert trials[1][0][0] == video3
    
    def test_classify_videos(self):
        """Test classifying videos in a folder"""
        classifier = VideoClassifier()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test video files
            video1 = temp_path / "20231201_120000-GoPro1234-test.MP4"
            video2 = temp_path / "20231201_120005-GoPro5678-test.MP4"
            video1.touch()
            video2.touch()
            
            result = classifier.classify_videos(temp_dir)
            
            assert len(result) == 1
            assert "20231201_120000" in result
            assert len(result["20231201_120000"]) == 2
    
    def test_classify_videos_folder_not_found(self):
        """Test classifying videos with non-existent folder"""
        classifier = VideoClassifier()
        
        with pytest.raises(ValueError, match="Video folder not found"):
            classifier.classify_videos("/non/existent/folder")
    
    def test_classify_videos_no_videos(self):
        """Test classifying videos with no videos"""
        classifier = VideoClassifier()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="No MP4 files found"):
                classifier.classify_videos(temp_dir)
    
    def test_get_trial_info(self):
        """Test getting trial information"""
        classifier = VideoClassifier()
        
        video1 = Path("video1.mp4")
        video2 = Path("video2.mp4")
        timestamp1 = datetime(2023, 12, 1, 12, 0, 0)
        timestamp2 = datetime(2023, 12, 1, 12, 0, 5)
        
        trial_videos = [(video1, timestamp1), (video2, timestamp2)]
        
        info = classifier.get_trial_info(trial_videos)
        
        assert info["trial_name"] == "20231201_120000"
        assert info["start_time"] == timestamp1
        assert info["end_time"] == timestamp2
        assert info["duration_seconds"] == 5.0
        assert info["video_count"] == 2
        assert info["first_video"] == str(video1)
        assert info["last_video"] == str(video2)
        assert len(info["all_videos"]) == 2
    
    def test_get_trial_info_empty(self):
        """Test getting trial info for empty trial"""
        classifier = VideoClassifier()
        
        info = classifier.get_trial_info([])
        assert info == {}
    
    def test_validate_videos(self):
        """Test video validation"""
        classifier = VideoClassifier()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid video file
            valid_video = temp_path / "20231201_120000-GoPro1234-test.MP4"
            valid_video.touch()
            
            # Create invalid (empty) video file
            invalid_video = temp_path / "empty.MP4"
            invalid_video.touch()
            
            # Create file with invalid format
            invalid_format = temp_path / "invalid_format.MP4"
            invalid_format.touch()
            
            result = classifier.validate_videos(temp_dir)
            
            assert len(result["valid"]) == 1
            assert str(valid_video) in result["valid"]
            assert len(result["invalid"]) == 2
            assert any("Empty file" in msg for msg in result["invalid"])
            assert any("Invalid filename format" in msg for msg in result["invalid"])
    
    def test_validate_videos_folder_not_found(self):
        """Test video validation with non-existent folder"""
        classifier = VideoClassifier()
        
        result = classifier.validate_videos("/non/existent/folder")
        
        assert len(result["valid"]) == 0
        assert len(result["invalid"]) == 1
        assert "Folder not found" in result["invalid"][0]
    
    def test_get_video_statistics(self):
        """Test getting video statistics"""
        classifier = VideoClassifier()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test video files
            video1 = temp_path / "video1.MP4"
            video2 = temp_path / "video2.MP4"
            
            # Write some data to simulate file sizes
            video1.write_bytes(b"x" * 1000)  # 1KB
            video2.write_bytes(b"x" * 2000)  # 2KB
            
            stats = classifier.get_video_statistics(temp_dir)
            
            assert stats["total_videos"] == 2
            assert stats["total_size_bytes"] == 3000
            assert stats["total_size_mb"] == pytest.approx(0.003, rel=1e-3)
            assert stats["average_size_mb"] == pytest.approx(0.0015, rel=1e-3)
    
    def test_get_video_statistics_no_videos(self):
        """Test getting video statistics with no videos"""
        classifier = VideoClassifier()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            stats = classifier.get_video_statistics(temp_dir)
            
            assert stats["total_videos"] == 0
            assert stats["total_size_bytes"] == 0
            assert stats["total_size_mb"] == 0


class TestVideoEncoder:
    """Test VideoEncoder functionality"""
    
    def test_init_ffmpeg(self):
        """Test initialization with FFmpeg backend"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            assert encoder.backend == EncoderBackend.FFMPEG
    
    def test_init_pyav(self):
        """Test initialization with PyAV backend"""
        with patch.object(VideoEncoder, '_check_pyav', return_value=True):
            encoder = VideoEncoder(EncoderBackend.PYAV)
            assert encoder.backend == EncoderBackend.PYAV
    
    def test_init_no_backend(self):
        """Test initialization with no available backend"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=False):
            with patch.object(VideoEncoder, '_check_pyav', return_value=False):
                with pytest.raises(RuntimeError, match="FFmpeg not found"):
                    VideoEncoder(EncoderBackend.FFMPEG)
    
    def test_check_ffmpeg_success(self):
        """Test FFmpeg availability check success"""
        encoder = VideoEncoder.__new__(VideoEncoder)  # Create without calling __init__
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = encoder._check_ffmpeg()
            assert result is True
    
    def test_check_ffmpeg_failure(self):
        """Test FFmpeg availability check failure"""
        encoder = VideoEncoder.__new__(VideoEncoder)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = encoder._check_ffmpeg()
            assert result is False
    
    def test_check_pyav_success(self):
        """Test PyAV availability check success"""
        encoder = VideoEncoder.__new__(VideoEncoder)
        
        with patch('builtins.__import__', return_value=Mock()):
            result = encoder._check_pyav()
            assert result is True
    
    def test_check_pyav_failure(self):
        """Test PyAV availability check failure"""
        encoder = VideoEncoder.__new__(VideoEncoder)
        
        with patch('builtins.__import__', side_effect=ImportError):
            result = encoder._check_pyav()
            assert result is False
    
    def test_transcode_dry_run(self):
        """Test transcoding in dry run mode"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                src = Path(temp_dir) / "input.mp4"
                dst = Path(temp_dir) / "output.mp4"
                src.touch()
                
                # Should not raise exception
                encoder.transcode(str(src), str(dst), dry_run=True)
    
    def test_transcode_source_not_found(self):
        """Test transcoding with non-existent source"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with pytest.raises(ValueError, match="Source file not found"):
                encoder.transcode("/non/existent.mp4", "/output.mp4")
    
    def test_transcode_destination_exists(self):
        """Test transcoding with existing destination"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                src = Path(temp_dir) / "input.mp4"
                dst = Path(temp_dir) / "output.mp4"
                src.touch()
                dst.touch()
                
                with pytest.raises(ValueError, match="Destination file already exists"):
                    encoder.transcode(str(src), str(dst))
    
    def test_transcode_ffmpeg_success(self):
        """Test successful FFmpeg transcoding"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                src = Path(temp_dir) / "input.mp4"
                dst = Path(temp_dir) / "output.mp4"
                src.touch()
                
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    
                    encoder.transcode(str(src), str(dst))
                    
                    # Check that subprocess was called with correct arguments
                    mock_run.assert_called_once()
                    args = mock_run.call_args[0][0]
                    assert "ffmpeg" in args
                    assert str(src) in args
                    assert str(dst) in args
    
    def test_transcode_ffmpeg_failure(self):
        """Test FFmpeg transcoding failure"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                src = Path(temp_dir) / "input.mp4"
                dst = Path(temp_dir) / "output.mp4"
                src.touch()
                
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 1
                    mock_run.return_value.stderr = "FFmpeg error"
                    
                    with pytest.raises(RuntimeError, match="FFmpeg failed"):
                        encoder.transcode(str(src), str(dst))
    
    def test_transcode_pyav_success(self):
        """Test successful PyAV transcoding"""
        with patch.object(VideoEncoder, '_check_pyav', return_value=True):
            encoder = VideoEncoder(EncoderBackend.PYAV)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                src = Path(temp_dir) / "input.mp4"
                dst = Path(temp_dir) / "output.mp4"
                src.touch()
                
                # Mock PyAV
                mock_container = Mock()
                mock_video_stream = Mock()
                mock_video_stream.width = 1920
                mock_video_stream.height = 1080
                mock_video_stream.rate = 30.0
                mock_container.streams.video = [mock_video_stream]
                mock_container.streams.audio = []
                mock_container.decode.return_value = []
                mock_container.close = Mock()
                
                mock_output_container = Mock()
                mock_output_stream = Mock()
                mock_output_stream.encode.return_value = Mock()
                mock_output_container.add_stream.return_value = mock_output_stream
                mock_output_container.mux = Mock()
                mock_output_container.close = Mock()
                
                with patch('builtins.__import__', return_value=Mock()):
                    with patch('av.open') as mock_open:
                        mock_open.side_effect = [mock_container, mock_output_container]
                        
                        encoder.transcode(str(src), str(dst))
                        
                        mock_open.assert_called()
                        mock_container.close.assert_called()
                        mock_output_container.close.assert_called()
    
    def test_get_video_info_ffmpeg(self):
        """Test getting video info with FFmpeg"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            mock_ffprobe_output = {
                "format": {"duration": "120.5", "size": "1000000"},
                "streams": [{
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "codec_name": "h264",
                    "bit_rate": "5000000"
                }]
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = json.dumps(mock_ffprobe_output)
                
                info = encoder.get_video_info("test.mp4")
                
                assert info["duration"] == 120.5
                assert info["size"] == 1000000
                assert info["width"] == 1920
                assert info["height"] == 1080
                assert info["fps"] == 30.0
                assert info["codec"] == "h264"
                assert info["bitrate"] == 5000000
    
    def test_get_video_info_pyav(self):
        """Test getting video info with PyAV"""
        with patch.object(VideoEncoder, '_check_pyav', return_value=True):
            encoder = VideoEncoder(EncoderBackend.PYAV)
            
            mock_container = Mock()
            mock_video_stream = Mock()
            mock_video_stream.width = 1920
            mock_video_stream.height = 1080
            mock_video_stream.rate = 30.0
            mock_video_stream.codec.name = "h264"
            mock_video_stream.bit_rate = 5000000
            mock_container.streams.video = [mock_video_stream]
            mock_container.duration = 120500000  # microseconds
            mock_container.close = Mock()
            
            with patch('builtins.__import__', return_value=Mock()):
                with patch('av.open', return_value=mock_container):
                    with patch('pathlib.Path.stat') as mock_stat:
                        mock_stat.return_value.st_size = 1000000
                        
                        info = encoder.get_video_info("test.mp4")
                        
                        assert info["width"] == 1920
                        assert info["height"] == 1080
                        assert info["fps"] == 30.0
                        assert info["codec"] == "h264"
                        assert info["bitrate"] == 5000000
                        mock_container.close.assert_called()
    
    def test_validate_video(self):
        """Test video validation"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with patch.object(encoder, 'get_video_info') as mock_get_info:
                mock_get_info.return_value = {
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0
                }
                
                result = encoder.validate_video("test.mp4")
                assert result is True
                
                mock_get_info.return_value = {
                    "width": 0,  # Invalid
                    "height": 1080,
                    "fps": 30.0
                }
                
                result = encoder.validate_video("test.mp4")
                assert result is False
    
    def test_get_supported_formats(self):
        """Test getting supported formats"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            formats = encoder.get_supported_formats()
            assert ".mp4" in formats
            assert ".avi" in formats
            assert ".mov" in formats
    
    def test_estimate_output_size(self):
        """Test output size estimation"""
        with patch.object(VideoEncoder, '_check_ffmpeg', return_value=True):
            encoder = VideoEncoder(EncoderBackend.FFMPEG)
            
            with patch.object(encoder, 'get_video_info') as mock_get_info:
                mock_get_info.return_value = {
                    "duration": 120.0,  # 2 minutes
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0
                }
                
                size = encoder.estimate_output_size("test.mp4", crf=18)
                assert size > 0
                
                # Test with exception
                mock_get_info.side_effect = Exception("Test error")
                size = encoder.estimate_output_size("test.mp4", crf=18)
                assert size > 0  # Should return fallback estimate
