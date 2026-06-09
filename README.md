<div align="center">

# 🧠 Kinesis CLI

**The Next-Generation Autonomous macOS Desktop Agent**

[![macOS](https://img.shields.io/badge/macOS-Apple_Silicon_Optimized-000000?style=for-the-badge&logo=apple&logoColor=white)](#)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Computer_Use-Powered-1A73E8?style=for-the-badge&logo=google&logoColor=white)](#)

*Kinesis translates high-level human directives into native macOS UI interactions in real-time, executing complex multi-step workflows visually.*

</div>

---

## ⚡ Overview
**Kinesis CLI** is a highly autonomous, intelligent macOS desktop agent designed to execute complex natural language directives directly on your computer. Powered by Google's state-of-the-art **Gemini 2.5 Computer Use** models, Kinesis operates just like a human: it looks at your screen, reasons about what it sees, and takes precise control of the mouse and keyboard to accomplish the mission.

Unlike traditional macro scripts or brittle RPA tools, Kinesis adapts dynamically to unexpected pop-ups, changing UI layouts, and unstructured web pages.

---

## 🌟 Premium Capabilities

### 🤖 True Autonomy & Chain of Thought
Give Kinesis an overarching goal (e.g., *"play a game of chess on chess.com and win"*). Kinesis natively breaks it down into granular sub-tasks, displays its internal **Chain of Thought (CoT)** reasoning live in the terminal, and executes the entire sequence of steps on its own.

### 🎯 Native OS Integration & Phantom Cursor
Built exclusively for macOS using PyObjC, CoreGraphics, and AppKit. Kinesis interacts directly with the lowest levels of the OS. It features a custom **Phantom Visual Cursor**—a dynamic purple pointer with fluid LERP-accelerated motion blur, sonar "ripple" click animations, and intelligent idle fading that travels seamlessly with you across Mission Control and Fullscreen Spaces.

### 🗣️ Voice TTS Mode
Enable Voice Mode (`/voice on`) to have Kinesis audibly speak its thought process out loud in real-time using native macOS text-to-speech, keeping you informed without needing to read the terminal!

### 📊 Comprehensive Mission Logging
Every action, thought, and sub-task is automatically logged (`/log on`). Kinesis generates comprehensive markdown reports after every mission, which you can easily review via the built-in `/list` and `/result` commands.

### 🛡️ Iron-Clad Fail-Safe
Kinesis is built with safety as a priority. If the agent begins acting unexpectedly, physically throw your real mouse to any corner of your screen (e.g., the top-left). This instantly triggers a hardware-level PyAutoGUI **Fail-Safe** and aborts all execution.

---

## 🛠️ Quick Start

### 1. Requirements
- **macOS** (Apple Silicon natively supported and highly recommended)
- **Python 3.10+**
- **System Permissions:** You must grant *Screen Recording* and *Accessibility* permissions to your Terminal/IDE.

### 2. Installation
```bash
git clone https://github.com/Louistuis/Kinesis.git
cd Kinesis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch & Interactive Setup
Just run Kinesis! On your first boot, an interactive **Setup Wizard** will gracefully guide you through configuring your API keys and generating a global `kinesis` terminal alias.
```bash
python main.py
```
*Kinesis supports both raw Gemini API Keys and local gcloud Application Default Credentials (OAuth)!*

---

## 🎮 Command Interface

Kinesis features a robust, auto-completing CLI environment. Below are some of the core slash commands you can use:

| Command | Description |
| :--- | :--- |
| **`/help`** | View all available slash commands. |
| **`/info`** | Show a detailed user manual and overview of Kinesis capabilities. |
| **`/status`** | View current system resolution, API model, and active toggles. |
| **`/voice on\|off`** | Toggle audible TTS chain-of-thought readouts. |
| **`/log on\|off`** | Toggle automatic mission logging and report generation. |
| **`/list`** | View a table of all your previously logged missions. |
| **`/result <id>`** | View the comprehensive final report of a specific mission. |
| **`/resume <id>`** | Instantly restore the agent's memory and tasks from a previous session! |
| **`/tasks <csv>`** | Manually inject tasks into the agent's Task Manager. |
| **`/update`** | Hot-reload the agent! Pulls the latest code from GitHub and restarts Kinesis without closing your terminal. |
| **`/setup`** | Restart the Authentication Wizard to switch API keys or modes. |

---

## 🚀 Usage Example

Once inside the dashboard, provide a natural language directive:

```text
🚀 DIRECTIVE > Open Safari, search for the latest Apple stock price, and summarize it for me.
```
Sit back, monitor the **Internal Brain** and **Task Manager** cards in your terminal, and watch Kinesis navigate the UI!

---

## ⚠️ Disclaimer
Kinesis is an experimental autonomous AI agent capable of taking full control of your mouse and keyboard. **Always supervise the agent during operation.** Be ready to trigger the Global Fail-Safe if the agent begins to exhibit unintended behavior.
