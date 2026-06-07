import sys
import time
sys.path.append("/Users/louis/Desktop/Kinesis")
from core.mac_os_bridge import MacBridge
import pyautogui

bridge = MacBridge()
screens = bridge.get_screens()
if len(screens) > 1:
    s2 = screens[1]
    print(f"Screen 2 found: {s2}")
    
    center_x = s2['x'] + s2['w']/2
    center_y = s2['y'] + s2['h']/2
    
    print(f"Moving to {center_x}, {center_y}")
    pyautogui.moveTo(center_x, center_y)
    
    pyautogui.click()
    time.sleep(0.5)
    
    print("Scrolling down...")
    bridge.execute_scroll_action(-100)
    time.sleep(1)
    
    print("Scrolling up...")
    bridge.execute_scroll_action(100)
    print("Done")
else:
    print("Only 1 screen detected!")
