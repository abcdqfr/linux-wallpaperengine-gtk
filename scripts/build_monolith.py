#!/usr/bin/env python3


import sys
from pathlib import Path


def build_monolith(src_dir: Path, output_file: Path) -> None:
    """Build a standalone monolith from src/ structure.""".

# Header for the monolith
    header = '''#!/usr/bin/env python3"""
Linux Wallpaper Engine GTK - Standalone Monolith
Built from modern src/ structure for distribution.

This file is auto-generated. For development, use the src/ structure.


if __name__ == "__main__":
    main()
Main build function."""
    src_dir = Path("src/wallpaperengine")
    output_file = Path("linux-wallpaperengine-gtk-standalone.py")

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        sys.exit(1)

    build_monolith(src_dir, output_file)

    # Make executable
    output_file.chmod(0o755)
    print(f"✅ Made executable: {output_file}")


if __name__ == "__main__":
    main()
