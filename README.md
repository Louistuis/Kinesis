<div align="center">

# 🧠 Kinesis CLI

**The Next-Generation Autonomous macOS Desktop Agent**

[![macOS](https://img.shields.io/badge/macOS-Apple_Silicon_Optimized-000000?style=for-the-badge&logo=apple&logoColor=white)](#)
[![Python & Node](https://img.shields.io/badge/Node.js%20&%20Python-Powered-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Gemini 3 Flash](https://img.shields.io/badge/Gemini_3_Flash-Powered-1A73E8?style=for-the-badge&logo=google&logoColor=white)](#)
[![NPM Version](https://img.shields.io/npm/v/kinesis-agent?style=for-the-badge&logo=npm&color=CB3837)](#)

> *Kinesis translates high-level human directives into native macOS UI interactions in real-time, executing complex multi-step workflows visually.*

</div>

<br>

## ⚡ The Agent that Actually Sees

**Kinesis CLI** is a highly autonomous, intelligent macOS desktop agent designed to execute complex natural language directives directly on your computer. Powered by Google's lightning-fast **Gemini 3 Flash** Computer Use model, Kinesis operates just like a human: it looks at your screen, reasons about what it sees, and takes precise control of your mouse and keyboard to accomplish the mission.

Unlike traditional macro scripts or brittle RPA tools, Kinesis adapts dynamically to unexpected pop-ups, changing UI layouts, and completely unstructured web pages.

---

## 🌟 Premium Capabilities

<table>
<tr>
<td width="50%">

### 🤖 True Autonomy & CoT
Give Kinesis an overarching goal (e.g., *"play chess on chess.com and win"*). Kinesis natively breaks it down into granular sub-tasks, displays its internal **Chain of Thought (CoT)** live in the terminal, and executes the sequence entirely on its own.

</td>
<td width="50%">

### 🎯 Phantom Visual Cursor
Built exclusively for macOS, Kinesis features a custom **Phantom Visual Cursor**—a dynamic purple pointer with fluid LERP-accelerated motion blur, sonar "ripple" click animations, and intelligent idle fading that travels seamlessly across Mission Control.

</td>
</tr>
<tr>
<td>

### 🗣️ Voice TTS Mode
Enable Voice Mode (`/voice on`) to have Kinesis audibly speak its thought process out loud in real-time using native macOS text-to-speech, keeping you informed without needing to stare at the terminal!

</td>
<td>

### 🛡️ Iron-Clad Fail-Safe
Kinesis is built with safety as a priority. If the agent begins acting unexpectedly, simply throw your physical mouse to any corner of your screen (e.g., the top-left). This instantly triggers a hardware-level **Fail-Safe** and aborts execution.

</td>
</tr>
</table>

---

## 🛠️ Lightning Fast Setup

We've completely eliminated the headache of managing Python virtual environments, cloning repositories, and manually installing requirements.

### 1. Prerequisites
- **macOS** (Apple Silicon natively supported and highly recommended)
- **Node.js** & **Python 3.10+**
- **Permissions:** You must grant *Screen Recording* and *Accessibility* permissions to your Terminal/IDE.

### 2. One-Line Installation
Install Kinesis globally using NPM:
```bash
npm install -g kinesis-agent
```

### 3. Launch & Interactive Setup
Just type the command below from anywhere on your Mac! On your first boot, an interactive **Setup Wizard** will gracefully guide you through configuring your Google Gemini API key or OAuth credentials.
```bash
kinesis
```
*Behind the scenes, the Node wrapper will instantly build the Python environment and proxy you into the native Agent CLI!*

---

## 🎮 Command Interface

Kinesis features a robust, auto-completing CLI environment. Below are the core slash commands you can use while inside the Kinesis terminal:

| Command | Description |
| :--- | :--- |
| **`/help`** | View all available slash commands. |
| **`/info`** | Show a detailed user manual and overview of Kinesis capabilities. |
| **`/status`** | View current system resolution, API model, and active toggles. |
| **`/screen <n>`** | Hot-swap the active monitor Kinesis operates on. |
| **`/speed <fast\|normal\|slow>`** | Change agent execution speed dynamically at runtime. |
| **`/pause`** | Toggle pause/resume of the agent loop mid-mission. |
| **`/history`** | Show a table of the last 20 actions from the current session. |
| **`/screenshot`** | Capture an instant screenshot and save it to the `screenshots/` directory. |
| **`/cost`** | View live estimated API cost, call count, and step count. |
| **`/model`** | Print the currently active AI model. |
| **`/voice on\|off`** | Toggle audible TTS chain-of-thought readouts. |
| **`/save on\|off`** | Toggle automatic mission logging and report generation. |
| **`/list`** | View a table of all your previously logged missions. |
| **`/result <id>`** | View the comprehensive final report of a specific mission. |
| **`/result log <id>`** | View the chronological actions taken in a specific mission. |
| **`/resume <id>`** | Instantly restore the agent's memory and tasks from a previous session! |
| **`/tasks <csv>`** | Manually inject tasks into the agent's Task Manager. |
| **`/update`** | Hot-reload the agent! Pulls the latest code from GitHub and restarts Kinesis without closing your terminal. |
| **`/setup`** | Restart the Authentication Wizard to switch API keys or modes. |

---

## 🖥️ The 5-Panel TUI Dashboard

Kinesis v1.1.0 introduces a massive, cyberpunk-themed 5-panel terminal UI that gives you god-mode visibility into the agent's brain:

1. **Header**: Live mission directive, elapsed timer, and step counter.
2. **⚡ Action Stream**: A color-coded, scrolling feed of the agent's precise physical actions (mouse clicks, keyboard typing, scrolling) with relative timestamps.
3. **🧠 Internal Brain**: The live, syntax-highlighted Chain of Thought (CoT) engine where Kinesis reasons about its next move.
4. **📋 Task Manager**: A dynamic checklist breaking down your overarching directive into actionable sub-tasks, complete with a visual progress bar and active task spinner.
5. **📊 System Vitals**: Real-time metrics tracking total steps, API calls, estimated session cost, and screen resolution.

---

## 🚀 Usage Example

Once inside the dashboard, provide a natural language directive:

```text
🚀 DIRECTIVE > Open Safari, search for the latest Apple stock price, and summarize it for me.
```
Sit back, monitor the **Internal Brain** and **Task Manager** cards in your terminal, and watch Kinesis navigate your Mac!

---

## ⚠️ Disclaimer
Kinesis is an experimental autonomous AI agent capable of taking full control of your mouse and keyboard. **Always supervise the agent during operation.** Be ready to trigger the Global Fail-Safe if the agent begins to exhibit unintended behavior.
