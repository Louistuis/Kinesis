import AppKit
import Quartz

# Requires CGWindowListCreate
window_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
for w in window_list:
    owner = w.get(Quartz.kCGWindowOwnerName, "")
    if owner == "Notes":
        print(w)
