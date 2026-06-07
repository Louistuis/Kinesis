import sys
from core.agent import MacAgent
import os
os.environ["GEMINI_API_KEY"] = "fake" # actually use the real one from config
import core.config
agent = MacAgent()
for event in agent.run("play chess with the bot."):
    if event["type"] == "error":
        print("ERROR:", event["message"])
        break
    else:
        print("EVENT:", event["type"], event.get("action_name", ""))
