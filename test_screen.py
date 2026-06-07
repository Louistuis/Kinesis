from core.mac_os_bridge import MacBridge
import AppKit

screens = AppKit.NSScreen.screens()
print("SCREENS:", len(screens))
for i, screen in enumerate(screens):
    frame = screen.frame()
    print(f"Screen {i}: x={frame.origin.x}, y={frame.origin.y}, w={frame.size.width}, h={frame.size.height}")

bridge = MacBridge()
for i in range(1, len(screens) + 1):
    bridge.set_active_screen(i)
    bbox = bridge.get_active_screen_bbox()
    print(f"BBOX {i}:", bbox)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=bbox)
        print(f"Image {i} size:", img.size)
    except Exception as e:
        print(f"ERROR {i}:", e)
