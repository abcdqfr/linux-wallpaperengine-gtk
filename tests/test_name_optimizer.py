"""Tests for name optimizer."""

import pytest
from src.wallpaperengine.name_optimizer import N

@pytest.fixture
def optimizer() -> N:
    """Create name optimizer instance."""
    return N()

def test_basic_conversion(optimizer: N) -> None:
    """Test basic pattern conversion."""
    text = "self.window = self.parent.current_widget"
    assert optimizer.c(text) == "ꜱ.ᴡ = ꜱ.ᴘ.ᴄᴡ"

def test_preserve_strings(optimizer: N) -> None:
    """Test string preservation."""
    text = 'logger.info("Current window size")'
    assert optimizer.c(text) == 'ʟ.ɪɴꜰ("Current window size")'

def test_preserve_comments(optimizer: N) -> None:
    """Test comment preservation."""
    text = "window = None  # Current window reference"
    assert optimizer.c(text) == "ᴡ = None  # Current window reference"

def test_preserve_reserved_words(optimizer: N) -> None:
    """Test reserved word preservation."""
    text = "if current in window and not is_valid:"
    assert optimizer.c(text) == "if ᴄ in ᴡ and not is_valid:"

def test_add_pattern(optimizer: N) -> None:
    """Test adding new pattern."""
    optimizer.ᴀ(r'\b(custom)\b', 'ᴋ')
    text = "custom.window"
    assert optimizer.c(text) == "ᴋ.ᴡ"

def test_remove_pattern(optimizer: N) -> None:
    """Test removing pattern."""
    optimizer.ᴅ(r'\b(window|widget)\b')
    text = "self.window"
    assert optimizer.c(text) == "ꜱ.window"

def test_multiline_code(optimizer: N) -> None:
    """Test multiline code conversion."""
    text = '''
def update_window(self):
    """Update current window."""
    self.logger.info("Updating window")
    self.current = self.parent.window
'''.strip()
    
    expected = '''
def ᴜᴡ(ꜱ):
    """Update current window."""
    ꜱ.ʟ.ɪɴꜰ("Updating window")
    ꜱ.ᴄ = ꜱ.ᴘ.ᴡ
'''.strip()
    
    assert optimizer.c(text) == expected

def test_mixed_content(optimizer: N) -> None:
    """Test mixed content conversion."""
    text = '''
# Window manager
class WindowManager:
    """Manage window state."""
    def __init__(self):
        self.logger = Logger("window")
        self.current = None  # Current window
'''.strip()
    
    expected = '''
# Window manager
class Wᴍ:
    """Manage window state."""
    def __init__(ꜱ):
        ꜱ.ʟ = Lɢ("window")
        ꜱ.ᴄ = None  # Current window
'''.strip()
    
    assert optimizer.c(text) == expected