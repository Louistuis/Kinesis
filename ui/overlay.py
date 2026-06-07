import AppKit
import objc
import sys

def show_overlays(screen_data_list):
    app = AppKit.NSApplication.sharedApplication()
    
    windows = []
    
    for (x, y, w, h, text) in screen_data_list:
        # Create window
        rect = AppKit.NSMakeRect(x, y, w, h)
        style_mask = AppKit.NSWindowStyleMaskBorderless
        
        window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style_mask, AppKit.NSBackingStoreBuffered, False
        )
        
        window.setOpaque_(False)
        window.setBackgroundColor_(AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.4))
        window.setLevel_(AppKit.NSFloatingWindowLevel)
        window.setIgnoresMouseEvents_(True)
        
        # Add text label
        label = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(0, h/2 - 100, w, 200))
        label.setStringValue_(text)
        label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(200))
        label.setTextColor_(AppKit.NSColor.whiteColor())
        label.setAlignment_(AppKit.NSTextAlignmentCenter)
        label.setDrawsBackground_(False)
        label.setBordered_(False)
        label.setEditable_(False)
        
        window.contentView().addSubview_(label)
        window.orderFrontRegardless()
        
        windows.append(window)
        
    # Stop after 3 seconds
    AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        3.0, app, objc.selector(app.terminate_, signature=b'v@:@'), None, False
    )
    
    app.run()

if __name__ == "__main__":
    # Arguments: x1 y1 w1 h1 text1 x2 y2 w2 h2 text2 ...
    args = sys.argv[1:]
    screen_data_list = []
    for i in range(0, len(args), 5):
        if i + 4 < len(args):
            x = float(args[i])
            y = float(args[i+1])
            w = float(args[i+2])
            h = float(args[i+3])
            text = args[i+4]
            screen_data_list.append((x, y, w, h, text))
            
    if screen_data_list:
        show_overlays(screen_data_list)
