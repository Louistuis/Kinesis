import AppKit
import Quartz
import threading
import time
import os

class CursorView(AppKit.NSView):
    def drawRect_(self, rect):
        AppKit.NSColor.clearColor().set()
        AppKit.NSRectFill(rect)
        
        path = AppKit.NSBezierPath.bezierPath()
        # Draw a custom red triangle cursor
        path.moveToPoint_(AppKit.NSMakePoint(0, 20))
        path.lineToPoint_(AppKit.NSMakePoint(15, 0))
        path.lineToPoint_(AppKit.NSMakePoint(5, 5))
        path.lineToPoint_(AppKit.NSMakePoint(0, 0))
        path.closePath()
        
        AppKit.NSColor.redColor().set()
        path.fill()

class CursorDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        rect = AppKit.NSMakeRect(0, 0, 20, 20)
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setLevel_(AppKit.NSScreenSaverWindowLevel)
        self.window.setIgnoresMouseEvents_(True)
        
        view = CursorView.alloc().initWithFrame_(rect)
        self.window.setContentView_(view)
        self.window.makeKeyAndOrderFront_(None)
        
        # Start a thread to read position
        threading.Thread(target=self.update_loop, daemon=True).start()

    def update_loop(self):
        while True:
            try:
                if os.path.exists('cursor_pos.txt'):
                    with open('cursor_pos.txt', 'r') as f:
                        data = f.read().strip().split(',')
                        if len(data) == 2:
                            x, y = float(data[0]), float(data[1])
                            
                            # Convert to AppKit coords
                            screen = AppKit.NSScreen.mainScreen()
                            h = screen.frame().size.height
                            appkit_y = h - y - 20
                            
                            AppKit.dispatch_async(AppKit.dispatch_get_main_queue(), lambda: self.window.setFrameOrigin_(AppKit.NSMakePoint(x, appkit_y)))
            except Exception:
                pass
            time.sleep(0.016) # ~60fps

app = AppKit.NSApplication.sharedApplication()
delegate = CursorDelegate.alloc().init()
app.setDelegate_(delegate)
app.run()
