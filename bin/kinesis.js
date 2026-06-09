#!/usr/bin/env node

const { spawnSync, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const kinesisDir = path.join(os.homedir(), '.kinesis');
const repoUrl = 'https://github.com/Louistuis/Kinesis.git';

function runCommand(command, args, cwd) {
    const result = spawnSync(command, args, { stdio: 'inherit', cwd: cwd });
    if (result.error) {
        console.error(`Error executing ${command}:`, result.error);
        process.exit(1);
    }
    if (result.status !== 0) {
        process.exit(result.status);
    }
}

// 1. Check if python3 and git are available
try {
    execSync('python3 --version', { stdio: 'ignore' });
    execSync('git --version', { stdio: 'ignore' });
} catch (e) {
    console.error("❌ Kinesis Error: 'python3' and 'git' must be installed and in your PATH.");
    process.exit(1);
}

// 2. Clone or pull latest code
if (!fs.existsSync(kinesisDir)) {
    console.log("🚀 Initializing Kinesis Agent (cloning from GitHub)...");
    runCommand('git', ['clone', repoUrl, kinesisDir], process.cwd());
} else {
    // Auto-update to latest master silently
    spawnSync('git', ['pull', 'origin', 'master'], { stdio: 'ignore', cwd: kinesisDir });
}

// 3. Setup Virtual Environment if it doesn't exist
const venvPath = path.join(kinesisDir, 'venv');
const venvPython = path.join(venvPath, 'bin', 'python3');
const venvPip = path.join(venvPath, 'bin', 'pip3');

if (!fs.existsSync(venvPath)) {
    console.log("   Creating virtual environment...");
    runCommand('python3', ['-m', 'venv', 'venv'], kinesisDir);
    
    console.log("   Installing dependencies (this may take a minute)...");
    runCommand(venvPip, ['install', '-r', 'requirements.txt'], kinesisDir);
    
    console.log("✅ Environment ready!\n");
} else {
    // Silently ensure requirements are up to date in case they changed
    spawnSync(venvPip, ['install', '-r', 'requirements.txt'], { stdio: 'ignore', cwd: kinesisDir });
}

// 4. Launch Kinesis
const mainPy = path.join(kinesisDir, 'main.py');
const args = process.argv.slice(2);

// Execute the Python script, replacing the Node process
runCommand(venvPython, [mainPy, ...args], kinesisDir);
