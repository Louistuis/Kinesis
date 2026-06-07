import Quartz
import time

def silent_click(x, y):
    # Save current position
    event = Quartz.CGEventCreate(None)
    current_pos = Quartz.CGEventGetLocation(event)
    
    # Create click event
    click_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
    )
    click_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
    )
    
    # Send click
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
    
    # Instantly restore position
    restore = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, current_pos, 0
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, restore)

# Get current mouse position
event = Quartz.CGEventCreate(None)
pos = Quartz.CGEventGetLocation(event)
print(f"Current pos: {pos}")

# Click far away
print("Clicking far away...")
silent_click(100, 100)

# Get pos again
event2 = Quartz.CGEventCreate(None)
pos2 = Quartz.CGEventGetLocation(event2)
print(f"Pos after: {pos2}")
