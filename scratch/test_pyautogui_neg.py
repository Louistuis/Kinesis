import pyautogui
import time
pyautogui.FAILSAFE = False
print(f"Current pos: {pyautogui.position()}")
pyautogui.moveTo(-100, 100)
print(f"New pos: {pyautogui.position()}")
