## [1.4.1](https://github.com/abcdqfr/linux-wallpaperengine-gtk/compare/v1.4.0...v1.4.1) (2026-05-06)


### Bug Fixes

* publish-tag-assets parses Forgejo JSON safely ([e5216cc](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/e5216cc9166ed1533d7da3ade4510fe8bd99fc86))

# [1.4.0](https://github.com/abcdqfr/linux-wallpaperengine-gtk/compare/v1.3.0...v1.4.0) (2026-05-06)


### Bug Fixes

* address bugbot release/mute issues ([611d193](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/611d1938e53ff218090e4dd46eb78d01489413e0))
* make quit deterministic and add e2e coverage ([39a45de](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/39a45de3875c13b33f6b158cd5bbe0fafa1cf93d))
* robust quit even with nested GTK loops ([6199909](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/6199909c64bd5d9ee3851744f0edebe921eaa19d))


### Features

* notify on wallpaper process exit; release notes metadata ([da59d73](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/da59d735aee36647ac74db975bee84fb6b7afcc9))
* verify scene.json only when referenced; context menu remove local files ([7db0c66](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/7db0c6675dcc9a16bcb4a3c427cc65fdc5d8f299))

# [1.3.0](https://github.com/abcdqfr/linux-wallpaperengine-gtk/compare/v1.2.2...v1.3.0) (2026-05-06)


### Bug Fixes

* make Docker containerization opt-in only ([a5d74ee](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/a5d74ee54a3eedfed65c55ac168b9842d672a152))
* use negative lookahead to exclude GTK app from process matching ([5c930b0](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/5c930b074ee92ca1962ccdaab482c38281bbdd9d))


### Features

* autodetect submodule-built engine; match upstream build docs ([2e32e92](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/2e32e928fccfb7d54ebc766cc7f2363aeeb2edfa))
* Freedesktop launcher plus CI reliability fixes ([2d0ce5c](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/2d0ce5c0bff022ee6b6043a577e532d4d990c79a))
* GNOME X11 compatibility via window-mode backend ([56b729f](https://github.com/abcdqfr/linux-wallpaperengine-gtk/commit/56b729f8f72da17ee66b694b9a2eb54f992e5634))
