"""Context menu implementation for wallpaper management.

Extracted from mature monolith v0.2.1.
"""

from gi.repository import Gtk


class WallpaperContextMenu(Gtk.Menu):
    """Context menu for wallpaper actions.

    Provides right-click menu options for applying wallpapers
    and managing playlists.
    """

    def __init__(self, parent, wallpaper_id):
        """Initialize the context menu.

        Args:
            parent: The parent window that owns this menu.
            wallpaper_id: The ID of the wallpaper this menu is for.
        """
        super().__init__()
        self.parent = parent
        self.wallpaper_id = wallpaper_id

        # Create menu items
        apply_item = Gtk.MenuItem(label="Apply Wallpaper")
        apply_item.connect("activate", self.on_apply_clicked)
        self.append(apply_item)

        playlist_item = Gtk.MenuItem(label="Add to Playlist")
        playlist_item.connect("activate", self.on_playlist_clicked)
        self.append(playlist_item)

        self.show_all()

    def on_apply_clicked(self, widget):
        """Apply the selected wallpaper to the desktop."""
        if self.parent.engine.run_wallpaper(self.wallpaper_id):
            self.parent.update_current_wallpaper(self.wallpaper_id)

    def on_playlist_clicked(self, widget):
        """Add wallpaper to playlist."""
        # Implementation will be added here
        print(f"Adding {self.wallpaper_id} to playlist")
