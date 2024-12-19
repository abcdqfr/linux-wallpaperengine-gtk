"""Tests for the Linux Wallpaper Engine GTK Frontend"""
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from wallpaperengine.main import PathManager, SettingsManager, WallpaperEngine

@pytest.fixture
def path_manager():
    """Create a PathManager instance for testing"""
    return PathManager()

@pytest.fixture
def settings_manager():
    """Create a SettingsManager instance for testing"""
    defaults = {
        'fps': 60,
        'volume': 100,
        'mute': False
    }
    return SettingsManager(defaults)

@pytest.fixture
def wallpaper_engine():
    """Create a WallpaperEngine instance for testing"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'HDMI-0\n'
        mock_run.return_value.returncode = 1  # No processes found
        engine = WallpaperEngine('/usr/bin/linux-wallpaperengine')  # Provide mock path
        yield engine

def test_path_manager_find_path(path_manager, tmp_path):
    """Test PathManager.find_path with temporary test paths"""
    # Create test paths
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    test_file = test_dir / "testfile"
    test_file.touch()
    
    # Test finding existing path
    paths = [str(test_file)]
    result = path_manager.find_path("test", paths)
    assert result == str(test_file)
    
    # Test non-existent path
    paths = ["/nonexistent/path"]
    result = path_manager.find_path("test", paths)
    assert result is None

def test_settings_manager_save_load(settings_manager, tmp_path):
    """Test SettingsManager save and load functionality"""
    # Override settings path for testing
    settings_manager.path = str(tmp_path / "settings.json")
    
    # Test saving settings
    settings_manager.set('fps', 30)
    assert settings_manager.save() is True
    
    # Create new settings manager with same path
    new_settings = SettingsManager({'fps': 60})
    new_settings.path = settings_manager.path
    
    # Force reload settings
    new_settings._load()
    assert new_settings.get('fps') == 30

def test_wallpaper_engine_detect_display(wallpaper_engine):
    """Test WallpaperEngine display detection"""
    assert wallpaper_engine.display == 'HDMI-0'

def test_wallpaper_engine_get_wallpapers(wallpaper_engine, tmp_path):
    """Test WallpaperEngine wallpaper listing"""
    # Create test wallpaper directory
    wallpaper_dir = tmp_path / "wallpapers"
    wallpaper_dir.mkdir()
    
    # Create test wallpaper files
    (wallpaper_dir / "123456").mkdir()
    (wallpaper_dir / "789012").mkdir()
    (wallpaper_dir / "not_a_number").mkdir()
    
    wallpaper_engine.wallpaper_dir = str(wallpaper_dir)
    wallpapers = wallpaper_engine._get_wallpapers()
    
    assert len(wallpapers) == 2
    assert "123456" in wallpapers
    assert "789012" in wallpapers
    assert "not_a_number" not in wallpapers

def test_wallpaper_engine_run_stop(wallpaper_engine):
    """Test WallpaperEngine run and stop functionality"""
    with patch('subprocess.Popen') as mock_popen, \
         patch('subprocess.run') as mock_run, \
         patch('os.chdir') as mock_chdir:
        
        # Mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Mock subprocess.run for stop() calls
        mock_run.return_value.returncode = 1  # No processes found
        
        # Test running wallpaper
        success, cmd = wallpaper_engine.run("123456", fps=60)
        assert success is True
        assert wallpaper_engine.current_wallpaper == "123456"
        assert wallpaper_engine.current_process is not None
        
        # Test stopping wallpaper
        assert wallpaper_engine.stop() is True
        assert wallpaper_engine.current_wallpaper is None
        assert wallpaper_engine.current_process is None