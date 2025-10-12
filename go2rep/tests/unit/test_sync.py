"""
Unit tests for synchronization engines
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

# Import core modules directly to avoid dependency issues
import sys
sys.path.insert(0, '/Users/a/Desktop/Go2Rep')

from go2rep.core.sync.timecode import TimecodeSyncEngine
from go2rep.core.sync.manual import ManualSyncEngine


class TestTimecodeSyncEngine:
    """Test TimecodeSyncEngine functionality"""
    
    def test_init(self):
        """Test initialization"""
        engine = TimecodeSyncEngine()
        assert engine.time_tolerance == 5
        
        engine = TimecodeSyncEngine(time_tolerance=10)
        assert engine.time_tolerance == 10
    
    def test_sync_trial_empty_list(self):
        """Test syncing empty video list"""
        engine = TimecodeSyncEngine()
        
        with pytest.raises(ValueError, match="No video paths provided"):
            engine.sync_trial([])
    
    def test_sync_trial_single_video(self):
        """Test syncing single video"""
        engine = TimecodeSyncEngine()
        
        # Mock the auto_synchronize_videos function
        mock_result = {
            "reference_video": "test_video.mp4",
            "start_frame_on_reference_video": 0,
            "end_frame_on_reference_video": 1000,
            "offsets": {"test_video.mp4": 0}
        }
        
        with patch('tools.timecode_synchronizer.auto_synchronize_videos') as mock_auto:
            mock_auto.return_value = mock_result
            
            result = engine.sync_trial(["test_video.mp4"])
            
            assert result == mock_result
            mock_auto.assert_called_once_with("single_trial", ["test_video.mp4"])
    
    def test_sync_trial_multiple_videos(self):
        """Test syncing multiple videos"""
        engine = TimecodeSyncEngine()
        
        mock_result = {
            "reference_video": "video1.mp4",
            "start_frame_on_reference_video": 0,
            "end_frame_on_reference_video": 1000,
            "offsets": {
                "video1.mp4": 0,
                "video2.mp4": 30,
                "video3.mp4": -15
            }
        }
        
        with patch('tools.timecode_synchronizer.auto_synchronize_videos') as mock_auto:
            mock_auto.return_value = mock_result
            
            result = engine.sync_trial(["video1.mp4", "video2.mp4", "video3.mp4"])
            
            assert result == mock_result
    
    def test_sync_trial_exception(self):
        """Test sync trial with exception"""
        engine = TimecodeSyncEngine()
        
        with patch('tools.timecode_synchronizer.auto_synchronize_videos') as mock_auto:
            mock_auto.side_effect = Exception("Test error")
            
            with pytest.raises(RuntimeError, match="Timecode synchronization failed"):
                engine.sync_trial(["test_video.mp4"])
    
    def test_sync_multiple_trials_folder_not_found(self):
        """Test syncing multiple trials with non-existent folder"""
        engine = TimecodeSyncEngine()
        
        with pytest.raises(ValueError, match="Video folder not found"):
            engine.sync_multiple_trials("/non/existent/folder")
    
    def test_sync_multiple_trials_no_videos(self):
        """Test syncing multiple trials with no videos"""
        engine = TimecodeSyncEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="No MP4 files found"):
                engine.sync_multiple_trials(temp_dir)
    
    def test_sync_multiple_trials_success(self):
        """Test successful multiple trials sync"""
        engine = TimecodeSyncEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock video files
            video1 = temp_path / "20231201_120000-GoPro1234-test.mp4"
            video2 = temp_path / "20231201_120005-GoPro5678-test.mp4"
            video1.touch()
            video2.touch()
            
            # Mock group_videos_by_trial to return our videos
            mock_trials = [[(video1, datetime(2023, 12, 1, 12, 0, 0)), 
                           (video2, datetime(2023, 12, 1, 12, 0, 5))]]
            
            mock_result = {
                "reference_video": str(video1),
                "start_frame_on_reference_video": 0,
                "end_frame_on_reference_video": 1000,
                "offsets": {str(video1): 0, str(video2): 30}
            }
            
            with patch('tools.timecode_synchronizer.group_videos_by_trial') as mock_group:
                with patch.object(engine, 'sync_trial') as mock_sync:
                    mock_group.return_value = mock_trials
                    mock_sync.return_value = mock_result
                    
                    result = engine.sync_multiple_trials(temp_dir)
                    
                    assert len(result) == 1
                    assert "20231201_120000" in result
                    assert result["20231201_120000"] == mock_result
    
    def test_get_video_metadata(self):
        """Test getting video metadata"""
        engine = TimecodeSyncEngine()
        
        mock_metadata = {
            "filename": "test_video.mp4",
            "creation_time": datetime(2023, 12, 1, 12, 0, 0),
            "timecode": "12:00:00:00",
            "fps": 30.0,
            "nb_frames": 1000
        }
        
        with patch('tools.timecode_synchronizer.ffprobe_metadata') as mock_ffprobe:
            with patch('tools.timecode_synchronizer.parse_timecode_to_seconds') as mock_parse:
                mock_ffprobe.return_value = mock_metadata
                mock_parse.return_value = 43200.0  # 12 hours in seconds
                
                result = engine.get_video_metadata("test_video.mp4")
                
                assert result["filename"] == "test_video.mp4"
                assert result["fps"] == 30.0
                assert result["timecode_seconds"] == 43200.0
    
    def test_get_video_metadata_exception(self):
        """Test getting video metadata with exception"""
        engine = TimecodeSyncEngine()
        
        with patch('tools.timecode_synchronizer.ffprobe_metadata') as mock_ffprobe:
            mock_ffprobe.side_effect = Exception("Test error")
            
            with pytest.raises(RuntimeError, match="Failed to get metadata"):
                engine.get_video_metadata("test_video.mp4")
    
    def test_validate_videos(self):
        """Test video validation"""
        engine = TimecodeSyncEngine()
        
        mock_metadata1 = {
            "timecode": "12:00:00:00",
            "creation_time": datetime(2023, 12, 1, 12, 0, 0)
        }
        
        mock_metadata2 = {
            "timecode": None,  # Missing timecode
            "creation_time": datetime(2023, 12, 1, 12, 0, 0)
        }
        
        with patch.object(engine, 'get_video_metadata') as mock_get_metadata:
            mock_get_metadata.side_effect = [
                mock_metadata1,  # Valid video
                mock_metadata2,  # Invalid video (no timecode)
                Exception("File error")  # Exception case
            ]
            
            result = engine.validate_videos(["video1.mp4", "video2.mp4", "video3.mp4"])
            
            assert len(result["valid"]) == 1
            assert result["valid"][0] == "video1.mp4"
            assert len(result["invalid"]) == 2
            assert "video2.mp4: No timecode metadata" in result["invalid"]
            assert "video3.mp4: File error" in result["invalid"]


class TestManualSyncEngine:
    """Test ManualSyncEngine functionality"""
    
    def test_init_default(self):
        """Test default initialization"""
        engine = ManualSyncEngine()
        assert engine.simulate is False
        assert engine.sample_json is None
        assert engine.filename_convention == 1
        assert engine.sample_data is None
    
    def test_init_simulation(self):
        """Test initialization with simulation mode"""
        engine = ManualSyncEngine(simulate=True, filename_convention=2)
        assert engine.simulate is True
        assert engine.filename_convention == 2
    
    def test_init_with_sample_json(self):
        """Test initialization with sample JSON"""
        sample_data = {
            "trial1": {
                "reference_video": "video1.mp4",
                "offsets": {"video1.mp4": 0, "video2.mp4": 30}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            sample_path = f.name
        
        try:
            engine = ManualSyncEngine(simulate=True, sample_json=sample_path)
            assert engine.sample_data == sample_data
        finally:
            Path(sample_path).unlink()
    
    def test_sync_trial_empty_list(self):
        """Test syncing empty video list"""
        engine = ManualSyncEngine()
        
        with pytest.raises(ValueError, match="No video paths provided"):
            engine.sync_trial([])
    
    def test_sync_trial_simulation_mode(self):
        """Test syncing in simulation mode"""
        engine = ManualSyncEngine(simulate=True)
        
        result = engine.sync_trial(["video1.mp4", "video2.mp4"])
        
        assert "reference_video" in result
        assert "offsets" in result
        assert "start_frame_on_reference_video" in result
        assert "end_frame_on_reference_video" in result
        
        # Check that reference video has 0 offset
        assert result["offsets"][result["reference_video"]] == 0
    
    def test_sync_trial_simulation_with_sample_data(self):
        """Test syncing in simulation mode with sample data"""
        sample_data = {
            "trial1": {
                "reference_video": "video1.mp4",
                "start_frame_on_reference_video": 100,
                "end_frame_on_reference_video": 1100,
                "offsets": {"video1.mp4": 0, "video2.mp4": 30}
            }
        }
        
        engine = ManualSyncEngine(simulate=True)
        engine.sample_data = sample_data
        
        result = engine.sync_trial(["video1.mp4", "video2.mp4"])
        
        assert result == sample_data["trial1"]
    
    def test_sync_trial_interactive_mode(self):
        """Test syncing in interactive mode"""
        engine = ManualSyncEngine(simulate=False)
        
        mock_result = {
            "reference_video": "video1.mp4",
            "start_frame_on_reference_video": 0,
            "end_frame_on_reference_video": 1000,
            "offsets": {"video1.mp4": 0, "video2.mp4": 30}
        }
        
        with patch('tools.manual_synchronizer.synchronize_videos') as mock_sync:
            mock_sync.return_value = mock_result
            
            result = engine.sync_trial(["video1.mp4", "video2.mp4"])
            
            assert result == mock_result
            mock_sync.assert_called_once_with("interactive_trial", ["video1.mp4", "video2.mp4"])
    
    def test_sync_trial_interactive_exception(self):
        """Test interactive sync with exception"""
        engine = ManualSyncEngine(simulate=False)
        
        with patch('tools.manual_synchronizer.synchronize_videos') as mock_sync:
            mock_sync.side_effect = Exception("Test error")
            
            with pytest.raises(RuntimeError, match="Interactive synchronization failed"):
                engine.sync_trial(["video1.mp4"])
    
    def test_sync_multiple_trials_folder_not_found(self):
        """Test syncing multiple trials with non-existent folder"""
        engine = ManualSyncEngine()
        
        with pytest.raises(ValueError, match="Video folder not found"):
            engine.sync_multiple_trials("/non/existent/folder")
    
    def test_sync_multiple_trials_no_videos(self):
        """Test syncing multiple trials with no videos"""
        engine = ManualSyncEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="No MP4 files found"):
                engine.sync_multiple_trials(temp_dir)
    
    def test_sync_multiple_trials_success(self):
        """Test successful multiple trials sync"""
        engine = ManualSyncEngine(simulate=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock video files
            video1 = temp_path / "20231201_120000-GoPro1234-test.MP4"
            video2 = temp_path / "20231201_120005-GoPro5678-test.MP4"
            video1.touch()
            video2.touch()
            
            # Mock group_videos_by_trial and parse_timestamp
            mock_trials = [[(video1, datetime(2023, 12, 1, 12, 0, 0)), 
                           (video2, datetime(2023, 12, 1, 12, 0, 5))]]
            
            with patch('tools.manual_synchronizer.group_videos_by_trial') as mock_group:
                with patch('tools.manual_synchronizer.parse_timestamp') as mock_parse:
                    with patch.object(engine, 'sync_trial') as mock_sync:
                        mock_group.return_value = mock_trials
                        mock_parse.return_value = datetime(2023, 12, 1, 12, 0, 0)
                        mock_sync.return_value = {"offsets": {"video1.mp4": 0}}
                        
                        result = engine.sync_multiple_trials(temp_dir)
                        
                        assert len(result) == 1
                        assert "20231201_120000" in result
    
    def test_validate_videos(self):
        """Test video validation"""
        engine = ManualSyncEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a valid video file
            valid_video = temp_path / "test.MP4"
            valid_video.touch()
            
            # Create an invalid (empty) video file
            invalid_video = temp_path / "empty.MP4"
            invalid_video.touch()
            
            # Mock open_video to simulate different behaviors
            def mock_open_video(path):
                if "empty" in str(path):
                    return None
                else:
                    mock_cap = Mock()
                    mock_cap.get.return_value = 1000  # frame count
                    return mock_cap
            
            with patch('tools.manual_synchronizer.open_video', side_effect=mock_open_video):
                result = engine.validate_videos([str(valid_video), str(invalid_video)])
                
                assert len(result["valid"]) == 1
                assert str(valid_video) in result["valid"]
                assert len(result["invalid"]) == 1
                assert "empty.MP4: Cannot open video file" in result["invalid"]
    
    def test_get_video_info(self):
        """Test getting video info"""
        engine = ManualSyncEngine()
        
        mock_cap = Mock()
        mock_cap.get.side_effect = [1000, 30.0, 1920, 1080]  # frame_count, fps, width, height
        
        with patch('tools.manual_synchronizer.open_video') as mock_open:
            mock_open.return_value = mock_cap
            
            result = engine.get_video_info("test.MP4")
            
            assert result["frame_count"] == 1000
            assert result["fps"] == 30.0
            assert result["width"] == 1920
            assert result["height"] == 1080
            assert result["duration"] == 1000 / 30.0
    
    def test_get_video_info_exception(self):
        """Test getting video info with exception"""
        engine = ManualSyncEngine()
        
        with patch('tools.manual_synchronizer.open_video') as mock_open:
            mock_open.return_value = None
            
            with pytest.raises(RuntimeError, match="Cannot open video file"):
                engine.get_video_info("test.MP4")
    
    def test_set_simulation_mode(self):
        """Test setting simulation mode"""
        engine = ManualSyncEngine(simulate=False)
        
        sample_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            sample_path = f.name
        
        try:
            engine.set_simulation_mode(True, sample_path)
            
            assert engine.simulate is True
            assert engine.sample_json == sample_path
            assert engine.sample_data == sample_data
        finally:
            Path(sample_path).unlink()
