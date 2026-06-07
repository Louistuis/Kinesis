# Kinesis CLI

## Overview
**Kinesis CLI** is a highly autonomous, intelligent macOS desktop agent designed to execute complex natural language directives directly on your computer. Powered by Google's state-of-the-art **Gemini 2.5 Computer Use** models, Kinesis translates high-level human goals into precise native UI interactions (mouse movements, clicks, keyboard events, and shell commands). 

Unlike traditional macro scripts or robotic process automation, Kinesis perceives your screen visually. It analyzes the UI on the fly and makes real-time, dynamic decisions to navigate apps, browse the web, and manage your system—just like a human would.

## 🌟 Key Features

- **True Autonomy**: Give it an overarching goal (e.g., *"play a game of chess on chess.com"*) and watch it reason, adapt to unexpected popups, and figure out the entire sequence of steps on its own.
- **Native macOS Integration**: Built exclusively for macOS using PyObjC, CoreGraphics, and AppKit. Kinesis interacts directly with the lowest levels of the OS for pixel-perfect precision and native system event generation.
- **Advanced Visual Cursor Engine**: Kinesis features its own dedicated, independently rendered phantom cursor (a sleek, dynamic purple Apple-style pointer). It includes fluid LERP-accelerated motion blur, sonar "ripple" clicking animations, and smart 10-second idle alpha fading.
- **Cross-Space Navigation**: The cursor overlay is injected directly into `NSScreenSaverWindowLevel`, allowing it to seamlessly travel with you across macOS Spaces, Mission Control, and Fullscreen applications.
- **Intelligent Translation Layer**: Intelligently intercepts and translates the Gemini AI's native deep-learning `computer_use` API outputs into custom native actions, eliminating hallucinations and ensuring rock-solid stability even when navigating continuous scroll views.
- **Global Fail-Safe**: Built-in, hardware-level mouse corner triggers to instantly abort any runaway agent actions with a simple flick of your real mouse.

## 🧠 How it Works
1. **Perception**: Kinesis quietly takes screenshots of your designated active monitor.
2. **Cognition**: The image and your directive are passed to the Gemini 2.5 Computer Use model. The AI reasons about the UI layout, determines its location, and decides the next optimal move.
3. **Execution**: The decision is sent back to the local Kinesis Executor, which translates it into precise CoreGraphics events. The visual phantom cursor physically glides to the target and executes the click or keystroke.
4. **Validation**: Kinesis verifies the result on the screen and repeats the loop until the overarching task is declared complete.

## 🛠️ Requirements
- macOS (Apple Silicon natively supported and recommended)
- Python 3.10+
- A Google Gemini API Key
- System Permissions: Screen Recording and Accessibility permissions must be granted to your Terminal/IDE.

## 🚀 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Kinesis.git
   cd Kinesis
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API Key:**
   Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_google_api_key_here
   ```

## 💻 Usage

Launch the agent by running:
```bash
python main.py
```
*(Pro tip: Set up a terminal alias so you can just type `kinesis`!)*

You will be presented with the Kinesis CLI dashboard. Select your target monitor, and provide a natural language directive:

```text
🚀 DIRECTIVE > Open Safari, search for the latest Apple stock price, and summarize it for me.
```
Sit back and watch Kinesis work!

## ⚠️ Disclaimer
Kinesis is an autonomous AI agent capable of taking control of your mouse and keyboard. **Always supervise the agent during operation.** Be ready to trigger the Global Fail-Safe (by rapidly pulling your real physical mouse to any corner of the screen) if the agent begins to exhibit unintended behavior.
