import sys
from core.agent import MacAgent
agent = MacAgent()
for event in agent.run("play chess with the bot on chess.com"):
    print(event)
    if event["type"] == "error":
        print("ERROR ENCOUNTERED!")
        break
