import AppKit
import threading
import time
import os
import json

class CursorView(AppKit.NSView):
    def drawRect_(self, rect):
        AppKit.NSColor.clearColor().set()
        AppKit.NSRectFill(rect)
        
        delegate = AppKit.NSApplication.sharedApplication().delegate()
        alpha = delegate.alpha
        
        if alpha <= 0:
            return
            
        # Draw Ripple
        if delegate.ripple_radius > 0:
            ripple_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
                AppKit.NSMakeRect(
                    64 - delegate.ripple_radius, 
                    64 - delegate.ripple_radius, 
                    delegate.ripple_radius * 2, 
                    delegate.ripple_radius * 2
                )
            )
            ripple_alpha = max(0, 1.0 - (delegate.ripple_radius / 40.0)) * alpha
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.2, 1.0, ripple_alpha).set()
            ripple_path.setLineWidth_(2.0)
            ripple_path.stroke()

        # Draw Trails (Motion Blur)
        for i, (gx, gy) in enumerate(delegate.history):
            lx = gx - delegate.current_x + 64
            ly = gy - delegate.current_y + 64
            trail_alpha = ((i + 1) / len(delegate.history)) * 0.4 * alpha
            self.draw_pointer(lx, ly, trail_alpha)

        # Draw Main Cursor
        self.draw_pointer(64, 64, alpha)
        
    def draw_pointer(self, cx, cy, alpha):
        path = AppKit.NSBezierPath.bezierPath()
        points = [
            (0, 32), (0, 4), (7, 11), (11, 0), (15, 2), (11, 13), (21, 13)
        ]
        
        for i, (px, py) in enumerate(points):
            nx = cx + px
            ny = cy + py - 32
            if i == 0:
                path.moveToPoint_(AppKit.NSMakePoint(nx, ny))
            else:
                path.lineToPoint_(AppKit.NSMakePoint(nx, ny))
        path.closePath()
        
        color1 = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.6, 0.0, 1.0, 0.9 * alpha)
        color2 = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.9, 0.4, 1.0, 0.9 * alpha)
        gradient = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(color1, color2)
        gradient.drawInBezierPath_angle_(path, -45.0)
        
        path.setLineWidth_(1.5)
        AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.9 * alpha).set()
        path.stroke()

class CursorDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        rect = AppKit.NSMakeRect(-5000, -5000, 128, 128)
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, AppKit.NSWindowStyleMaskBorderless, AppKit.NSBackingStoreBuffered, False
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setLevel_(AppKit.NSScreenSaverWindowLevel)
        self.window.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces | AppKit.NSWindowCollectionBehaviorStationary)
        self.window.setIgnoresMouseEvents_(True)
        
        self.view = CursorView.alloc().initWithFrame_(rect)
        self.window.setContentView_(self.view)
        self.window.makeKeyAndOrderFront_(None)
        
        self.last_mod_time = 0
        self.target_x = -5000
        self.target_y = -5000
        self.current_x = -5000
        self.current_y = -5000
        
        self.alpha = 0.0
        self.state = "idle"
        self.ripple_radius = 0.0
        self.history = [] 
        
        self.idle_start_time = time.time()
        
        threading.Thread(target=self.file_poll_loop, daemon=True).start()
        threading.Thread(target=self.render_loop, daemon=True).start()

    def file_poll_loop(self):
        cursor_file = 'cursor_pos.txt'
        while True:
            try:
                if os.path.exists(cursor_file):
                    mod_time = os.path.getmtime(cursor_file)
                    if mod_time > self.last_mod_time:
                        self.last_mod_time = mod_time
                        with open(cursor_file, 'r') as f:
                            raw = f.read().strip()
                            if raw.startswith("{"):
                                data = json.loads(raw)
                                new_state = data.get("state", "idle")
                                
                                if new_state != self.state:
                                    self.state = new_state
                                    if self.state == "idle":
                                        self.idle_start_time = time.time()
                                
                                if self.state in ["moving", "clicking"]:
                                    x = data.get("x", self.target_x)
                                    y = data.get("y", -5000)
                                    
                                    if y != -5000:
                                        screen = AppKit.NSScreen.mainScreen()
                                        primary_h = screen.frame().size.height
                                        appkit_y = primary_h - y
                                        
                                        self.target_x = x
                                        self.target_y = appkit_y
                                        
                                        if self.current_x == -5000:
                                            self.current_x = self.target_x
                                            self.current_y = self.target_y
                                            
                                if self.state == "clicking":
                                    self.ripple_radius = 1.0
            except Exception:
                pass
            time.sleep(0.05)

    def render_loop(self):
        while True:
            needs_redraw = False
            
            if self.state == "idle":
                # Wait 10 seconds before hiding
                if time.time() - self.idle_start_time > 10.0:
                    if self.alpha > 0:
                        self.alpha -= 0.05
                        needs_redraw = True
            else:
                if self.alpha < 1.0:
                    self.alpha += 0.2
                    needs_redraw = True
                    
            self.alpha = max(0.0, min(1.0, self.alpha))
            
            if self.current_x != -5000 and self.alpha > 0:
                if self.ripple_radius > 0:
                    self.ripple_radius += 2.0
                    needs_redraw = True
                    if self.ripple_radius > 40:
                        self.ripple_radius = 0
                        
                dx = self.target_x - self.current_x
                dy = self.target_y - self.current_y
                dist = (dx*dx + dy*dy)**0.5
                
                if dist > 0.5:
                    self.history.append((self.current_x, self.current_y))
                    if len(self.history) > 6:
                        self.history.pop(0)
                        
                    self.current_x += dx * 0.35
                    self.current_y += dy * 0.35
                    needs_redraw = True
                else:
                    if len(self.history) > 0:
                        self.history.pop(0)
                        needs_redraw = True
                        
                if needs_redraw:
                    import PyObjCTools.AppHelper
                    win_x = self.current_x - 64
                    win_y = self.current_y - 64
                    PyObjCTools.AppHelper.callAfter(self.window.setFrameOrigin_, AppKit.NSMakePoint(win_x, win_y))
                    PyObjCTools.AppHelper.callAfter(self.view.setNeedsDisplay_, True)
                    
            time.sleep(0.016)

if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    delegate = CursorDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()
