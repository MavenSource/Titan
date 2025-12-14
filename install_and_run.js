#!/usr/bin/env node
/**
 * Cross-platform one-click installer and runner
 * Detects OS and runs appropriate installation script
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Detect operating system
const isWindows = process.platform === 'win32';
const isMac = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

console.log('🚀 Titan One-Click Installer');
console.log('Platform:', process.platform);
console.log('');

// Check if .env exists
if (!fs.existsSync('.env')) {
    console.log('⚠️  .env file not found');
    if (fs.existsSync('.env.example')) {
        console.log('Creating .env from .env.example...');
        fs.copyFileSync('.env.example', '.env');
        console.log('✅ .env file created');
        console.log('');
        console.log('⚠️  IMPORTANT: Edit .env file with your configuration:');
        console.log('   - Add your PRIVATE_KEY');
        console.log('   - Add RPC endpoints (Infura/Alchemy API keys)');
        console.log('   - Add LIFI_API_KEY');
        console.log('   - Configure EXECUTION_MODE (PAPER or LIVE)');
        console.log('');
        process.exit(1);
    } else {
        console.error('❌ .env.example not found');
        process.exit(1);
    }
}

console.log('✅ .env file exists');
console.log('');

// Run platform-specific script
try {
    if (isWindows) {
        console.log('Running Windows installation...');
        console.log('Note: This will start the system in the current terminal.');
        console.log('For separate windows, use run_titan.bat instead.');
        console.log('');
        
        // Run commands sequentially
        console.log('[1/4] Installing Node.js dependencies...');
        execSync('npm install --legacy-peer-deps', { stdio: 'inherit' });
        
        console.log('[2/4] Installing Python dependencies...');
        execSync('pip install -r requirements.txt', { stdio: 'inherit' });
        
        console.log('[3/4] Compiling smart contracts...');
        execSync('npx hardhat compile', { stdio: 'inherit' });
        
        console.log('[4/4] Starting system...');
        console.log('');
        console.log('⚠️  Starting in current terminal. Press Ctrl+C to stop.');
        console.log('For separate windows, use run_titan.bat instead.');
        console.log('');
        
        // Start Brain in background
        const { spawn } = require('child_process');
        const brain = spawn('python', ['ml/brain.py'], {
            stdio: 'inherit',
            detached: false
        });
        
        // Wait a bit then start executor
        setTimeout(() => {
            const executor = spawn('node', ['execution/bot.js'], {
                stdio: 'inherit',
                detached: false
            });
            
            process.on('SIGINT', () => {
                console.log('\\nStopping Titan...');
                brain.kill();
                executor.kill();
                process.exit();
            });
        }, 2000);
        
    } else {
        // Unix-like systems (Linux/macOS)
        console.log('Running Unix/Linux installation...');
        
        const scriptPath = path.join(__dirname, 'run_titan.sh');
        if (!fs.existsSync(scriptPath)) {
            console.error('❌ run_titan.sh not found');
            process.exit(1);
        }
        
        // Make executable
        fs.chmodSync(scriptPath, '755');
        
        // Run the script
        execSync('./run_titan.sh', { stdio: 'inherit' });
    }
} catch (error) {
    console.error('❌ Installation failed:', error.message);
    process.exit(1);
}
