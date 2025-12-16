# Windows Installation Guide

This guide provides Windows-specific installation instructions and troubleshooting for Titan.

## Prerequisites

### Required Software

1. **Node.js 18+**
   - Download from: https://nodejs.org/
   - Verify installation: `node -v`

2. **Python 3.8+**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Verify installation: `python --version` or `python3 --version`

3. **Git for Windows**
   - Download from: https://git-scm.com/download/win
   - Use default settings during installation

4. **Visual Studio Build Tools** (for some Python packages)
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++" workload
   - Required for packages like `rustworkx`

## Installation Steps

### 1. Run as Administrator

Many installation commands require elevated privileges on Windows:

1. Right-click on **Command Prompt** or **PowerShell**
2. Select **"Run as Administrator"**
3. Navigate to the project directory

### 2. Install Dependencies

#### Option A: Using npm (Recommended for Windows)

```bash
npm install --legacy-peer-deps
```

The `--legacy-peer-deps` flag resolves peer dependency conflicts.

#### Option B: Using Yarn

If you encounter permission errors with Yarn:

1. Enable script execution in PowerShell (run as Administrator):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. Install dependencies:
   ```bash
   yarn install
   ```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or if you have multiple Python versions:

```bash
python -m pip install -r requirements.txt
```

### 4. Compile Smart Contracts

```bash
npx hardhat compile
```

## Common Issues and Solutions

### Issue: "python3: command not found"

**Cause**: Windows uses `python` instead of `python3` by default.

**Solution**: The npm scripts have been updated to use `python` instead of `python3`. If you still encounter issues:

1. Create an alias (PowerShell):
   ```powershell
   New-Alias python3 python

2. Or use the full path:
   ```bash
   python ml/brain.py
   ```

### Issue: "Cannot read properties of undefined (reading 'getContractFactory')"

**Cause**: Hardhat ethers plugin not loaded properly.

**Solution**: 
1. Verify `hardhat.config.js` has the toolbox uncommented:
   ```javascript
   require("@nomicfoundation/hardhat-toolbox");
   ```

2. Reinstall dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```

3. Clear cache and recompile:
   ```bash
   npx hardhat clean
   npx hardhat compile
   ```

### Issue: Yarn Permission Errors

**Cause**: Windows script execution policies.

**Solution**:
1. Run PowerShell as Administrator
2. Enable script execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. Or use npm instead of Yarn

### Issue: Redis Connection Errors

**Cause**: Redis is not available by default on Windows.

**Solutions**:

#### Option 1: Use Redis on Windows (WSL)
1. Install Windows Subsystem for Linux (WSL2)
2. Install Redis in WSL:
   ```bash
   sudo apt-get update
   sudo apt-get install redis-server
   sudo service redis-server start
   ```

#### Option 2: Use Redis Docker Container
1. Install Docker Desktop for Windows
2. Run Redis:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

#### Option 3: Use Memurai (Redis Alternative)
1. Download from: https://www.memurai.com/
2. Install and start the service
3. Use default connection settings

#### Option 4: Run in Paper Trading Mode (No Redis Required)
Set in your `.env` file:
```
EXECUTION_MODE=PAPER
```

### Issue: "npm ERR! ENOENT: no such file or directory"

**Cause**: Build artifacts or cache corruption.

**Solution**:
1. Clean all artifacts:
   ```bash
   npx hardhat clean
   ```

2. Delete node_modules and reinstall:
   ```bash
   rmdir /s /q node_modules
   npm install --legacy-peer-deps
   ```

### Issue: Visual Studio Build Tools Required

**Cause**: Some Python packages need C++ compilation.

**Solution**:
1. Install Visual Studio Build Tools
2. Select "Desktop development with C++" workload
3. Reinstall Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Issue: Path Too Long Error

**Cause**: Windows has a 260 character path limit.

**Solution**:
1. Enable long paths (Windows 10+, run as Administrator):
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

2. Or move the project to a shorter path like `C:\Titan`

### Issue: Hardhat Network Connection Timeout

**Cause**: Windows Firewall blocking connections.

**Solution**:
1. Add Node.js to Windows Firewall exceptions
2. Or temporarily disable firewall for testing:
   - Go to Windows Security > Firewall & network protection
   - Turn off firewall (for testing only)

## Environment Variables

### Setting Environment Variables

#### PowerShell:
```powershell
$env:PRIVATE_KEY="0x..."
$env:EXECUTION_MODE="PAPER"
```

#### Command Prompt:
```cmd
set PRIVATE_KEY=0x...
set EXECUTION_MODE=PAPER
```

#### Permanent (via .env file - Recommended):
Create a `.env` file in the project root:
```
PRIVATE_KEY=0x...
EXECUTION_MODE=PAPER
RPC_POLYGON=https://polygon-rpc.com
```

## Running the Bot

### Paper Trading Mode (Recommended for Testing)
```bash
npm start
```

Make sure `.env` has:
```
EXECUTION_MODE=PAPER
```

### Live Trading Mode (Requires Real Funds)
```bash
npm start
```

Make sure `.env` has:
```
EXECUTION_MODE=LIVE
PRIVATE_KEY=0x...
EXECUTOR_ADDRESS=0x...
```

## Testing Installation

### 1. Verify Node.js and Python
```bash
npm run health
```

Expected output:
```
v18.x.x (or higher)
Python 3.x.x (or higher)
```

### 2. Compile Contracts
```bash
npm run compile
```

Expected output:
```
Compiled 1 Solidity file successfully
```

### 3. Run Tests (if available)
```bash
npm test
```

## Tips for Windows Users

1. **Use Windows Terminal**: Better than Command Prompt, supports tabs and modern features
   - Download from Microsoft Store

2. **Use Git Bash**: Comes with Git for Windows, provides Unix-like commands
   - Useful for running shell scripts

3. **VS Code Terminal**: If using VS Code, the integrated terminal handles paths better
   - Use Ctrl+` to open terminal

4. **Path Separators**: Windows uses backslashes (`\`), but most Node.js tools accept forward slashes (`/`)

5. **Case Sensitivity**: Windows is case-insensitive for file names, but be consistent for cross-platform compatibility

## Getting Help

If you encounter issues not covered here:

1. Check the main README.md for general troubleshooting
2. Review error messages carefully - they often indicate the solution
3. Search GitHub Issues: https://github.com/MavenSource/Titan/issues
4. Open a new issue with:
   - Your Windows version
   - Node.js version (`node -v`)
   - Python version (`python --version`)
   - Complete error message
   - Steps to reproduce

## Security Notes

⚠️ **NEVER commit your `.env` file or share your `PRIVATE_KEY`**

- The `.env` file contains sensitive credentials
- Add `.env` to `.gitignore` (already included)
- Use a separate wallet for testing
- Start with Paper Trading mode before using real funds

## Next Steps

After successful installation:

1. Review `QUICKSTART.md` for usage instructions
2. Read `README.md` for system architecture
3. Check `OPERATIONS_GUIDE.md` for advanced configuration
4. Test in Paper Trading mode before going live
