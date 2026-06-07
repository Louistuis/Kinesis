import sys
import logging
from core.agent import MacAgent
agent = MacAgent()
for event in agent.run("play chess with the bot"):
    print("EVENT:", event)
    if event["type"] == "error":
        print("ERROR ENCOUNTERED!", event)
        break
