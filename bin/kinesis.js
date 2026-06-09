#!/usr/bin/env node

const { spawnSync, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// The directory where the npm package is installed
const projectRoot = path.join(__dirname, '..');
const venvPath = path.join(projectRoot, 'venv');
const venvPython = path.join(venvPath, 'bin', 'python3');
const venvPip = path.join(venvPath, 'bin', 'pip3');

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

// 1. Check if python3 is available
try {
    execSync('python3 --version', { stdio: 'ignore' });
} catch (e) {
    console.error("❌ Kinesis Error: 'python3' is not installed or not in your PATH.");
    console.error("Please install Python 3.10+ before running Kinesis.");
    process.exit(1);
}

// 2. Setup Virtual Environment if it doesn't exist
if (!fs.existsSync(venvPath)) {
    console.log("🚀 First time setup: Initializing Kinesis Python environment...");
    try {
        console.log("   Creating virtual environment...");
        runCommand('python3', ['-m', 'venv', 'venv'], projectRoot);
        
        console.log("   Installing dependencies (this may take a minute)...");
        runCommand(venvPip, ['install', '-r', 'requirements.txt'], projectRoot);
        
        console.log("✅ Environment ready!\n");
    } catch (error) {
        console.error("❌ Failed to set up Kinesis environment.");
        process.exit(1);
    }
}

// 3. Launch Kinesis
const mainPy = path.join(projectRoot, 'main.py');
// We pass any additional arguments passed to the CLI directly to Python
const args = process.argv.slice(2);

// Execute the Python script, replacing the Node process
runCommand(venvPython, [mainPy, ...args], projectRoot);
