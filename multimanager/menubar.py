"""macOS menu bar via pystray — must run from main thread."""
import os, webbrowser


def run_menubar(port):
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("[menubar] pystray/Pillow not installed — no tray icon")
        return

    def make_icon():
        img = Image.new("RGBA", (22, 22), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([2, 2, 20, 20], radius=4, fill=(59, 130, 246, 255))
        for x, y in [(6, 6), (12, 6), (6, 12), (12, 12)]:
            d.rounded_rectangle([x, y, x + 4, y + 4], radius=1, fill=(255, 255, 255, 255))
        return img

    def on_open(icon, item):
        webbrowser.open(f"http://127.0.0.1:{port}")

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon(
        "MultiManager",
        icon=make_icon(),
        menu=pystray.Menu(
            pystray.MenuItem("Open", on_open),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        ),
    )
    icon.run()
