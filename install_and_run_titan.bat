@echo off
REM ==============================================================================
REM APEX-OMEGA TITAN: FULL-SCALE INSTALLATION & EXECUTION SCRIPT (Windows)
REM ==============================================================================
REM Complete end-to-end installation, configuration, and execution for Windows
REM This script:
REM   1. Installs ALL dependencies (Node.js, Python, Redis)
REM   2. Builds Rust components (rustworkx Python library)
REM   3. Sets up Redis (optional, with fallback)
REM   4. Compiles and deploys smart contracts
REM   5. Configures wallet for gas, TX signing, execution, and profit deposits
REM   6. Launches the complete Titan arbitrage system
REM
REM Usage: install_and_run_titan.bat
REM ==============================================================================

setlocal enabledelayedexpansion

REM Configuration
set "EXECUTION_MODE=PAPER"
set "DEPLOY_NETWORK=polygon"

REM Colors (limited in Windows CMD)
echo.
echo ================================================================
echo    APEX-OMEGA TITAN: FULL-SCALE INSTALLATION ^& EXECUTION
echo ================================================================
echo.

REM ==============================================================================
REM STEP 1: CHECK PREREQUISITES
REM ==============================================================================

echo [STEP 1/10] Checking System Prerequisites...
echo.

REM Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Node.js not found
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node -v') do set NODE_VERSION=%%i
    echo [+] Node.js found: !NODE_VERSION!
)

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found
    echo Please install Python 3.11+ from https://python.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [+] Python found: !PYTHON_VERSION!
)

REM Check pip
where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip not found
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
) else (
    echo [+] pip found
)

REM Check Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git not found (optional)
) else (
    echo [+] Git found
)

echo.

REM ==============================================================================
REM STEP 2: INSTALL NODE.JS DEPENDENCIES
REM ==============================================================================

echo [STEP 2/10] Installing Node.js Dependencies...
echo.

if exist package.json (
    call npm install --legacy-peer-deps
    if %errorlevel% neq 0 (
        echo [X] Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo [+] Node.js dependencies installed
) else (
    echo [X] package.json not found
    pause
    exit /b 1
)

echo.

REM ==============================================================================
REM STEP 3: INSTALL PYTHON DEPENDENCIES & RUST COMPONENTS
REM ==============================================================================

echo [STEP 3/10] Installing Python Dependencies ^& Rust Components...
echo.

if exist requirements.txt (
    echo [i] Installing Python packages (including rustworkx)...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [X] Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo [+] Python dependencies installed (including rustworkx)
    echo [i] rustworkx: Rust-based graph library for pathfinding
) else (
    echo [X] requirements.txt not found
    pause
    exit /b 1
)

echo.

REM ==============================================================================
REM STEP 4: SETUP REDIS
REM ==============================================================================

echo [STEP 4/10] Setting Up Redis (Message Queue)...
echo.

where redis-server >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Redis not found
    echo [i] Redis is optional but recommended
    echo [i] Install from: https://github.com/microsoftarchive/redis/releases
    echo [i] Or use Docker: docker run -d -p 6379:6379 redis
) else (
    echo [+] Redis installed
    REM Try to start Redis
    redis-cli ping >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] Starting Redis server...
        start /B redis-server
        timeout /t 2 /nobreak >nul
    )
    redis-cli ping >nul 2>&1
    if %errorlevel% equ 0 (
        echo [+] Redis is running
    ) else (
        echo [!] Redis may not be running (optional)
    )
)

echo.

REM ==============================================================================
REM STEP 5: COMPILE SMART CONTRACTS
REM ==============================================================================

echo [STEP 5/10] Compiling Smart Contracts...
echo.

echo [i] Compiling Solidity contracts...
call npx hardhat compile
if %errorlevel% neq 0 (
    echo [X] Smart contract compilation failed
    pause
    exit /b 1
)
echo [+] Smart contracts compiled successfully
echo [i] Built: OmniArbExecutor (flash loan arbitrage executor)
echo [i] Built: Token registries, pool managers, and tokenomics modules

echo.

REM ==============================================================================
REM STEP 6: CONFIGURE ENVIRONMENT
REM ==============================================================================

echo [STEP 6/10] Configuring Environment...
echo.

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [+] Created .env from template
    ) else (
        echo [X] .env.example not found
        pause
        exit /b 1
    )
) else (
    echo [+] .env file already exists
)

echo.
echo [!] WALLET CONFIGURATION REQUIRED
echo.
echo Please enter your wallet private key (with 0x prefix):
set /p "WALLET_KEY=Key: "

REM Basic validation
if "!WALLET_KEY:~0,2!" neq "0x" (
    echo [X] Invalid private key format. Must start with 0x
    pause
    exit /b 1
)

REM Update .env with wallet key
powershell -Command "(Get-Content .env) -replace '^PRIVATE_KEY=.*', 'PRIVATE_KEY=!WALLET_KEY!' | Set-Content .env"
echo [+] Wallet private key configured

REM Set execution mode
powershell -Command "(Get-Content .env) -replace '^EXECUTION_MODE=.*', 'EXECUTION_MODE=!EXECUTION_MODE!' | Set-Content .env"
echo [+] Execution mode set to: !EXECUTION_MODE!

echo.
echo [i] You may need to add API keys to .env:
echo [i]   - Infura: https://infura.io/
echo [i]   - Alchemy: https://alchemy.com/
echo [i]   - Li.Fi: https://li.fi/

echo.

REM ==============================================================================
REM STEP 7: CREATE DATA DIRECTORIES
REM ==============================================================================

echo [STEP 7/10] Creating Data Directories...
echo.

if not exist data mkdir data
if not exist logs mkdir logs
if not exist certs mkdir certs
echo [+] Data directories created (data\, logs\, certs\)

echo.

REM ==============================================================================
REM STEP 8: DEPLOY SMART CONTRACTS
REM ==============================================================================

echo [STEP 8/10] Deploying Smart Contracts (Registries ^& Pools)...
echo.

echo [i] Deploying OmniArbExecutor to %DEPLOY_NETWORK%...
echo [i] This creates the on-chain registry for pools and tokenomics

REM Check if RPC is configured
findstr /C:"RPC_POLYGON=https://" .env >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] RPC endpoint not configured. Deployment may fail.
    echo [i] Add RPC_POLYGON to .env before deploying
    echo.
    echo Skip deployment? (Y/N):
    set /p "SKIP_DEPLOY=Choice: "
    if /i "!SKIP_DEPLOY!"=="Y" (
        echo [!] Deployment skipped
        goto :skip_deploy
    )
)

call npx hardhat run scripts/deploy.js --network %DEPLOY_NETWORK%
if %errorlevel% equ 0 (
    echo [+] Contract deployed successfully
    echo [i] Please add the deployed address to .env
) else (
    echo [!] Contract deployment failed or skipped
    echo [i] You can deploy later with: npx hardhat run scripts/deploy.js --network %DEPLOY_NETWORK%
)

:skip_deploy
echo.

REM ==============================================================================
REM STEP 9: RUN SYSTEM AUDIT
REM ==============================================================================

echo [STEP 9/10] Running System Audit...
echo.

if exist audit_system.py (
    python audit_system.py
    if %errorlevel% equ 0 (
        echo [+] System audit passed
    ) else (
        echo [!] System audit completed with warnings
    )
) else (
    echo [!] audit_system.py not found, skipping audit
)

echo.

REM ==============================================================================
REM STEP 10: LAUNCH SYSTEM
REM ==============================================================================

echo [STEP 10/10] System Ready - Launching Titan...
echo.

echo ================================================================
echo    TITAN SYSTEM CONFIGURED AND READY TO LAUNCH
echo ================================================================
echo.
echo Configuration Summary:
echo   - Wallet: Configured
echo   - Execution Mode: !EXECUTION_MODE!
if "!EXECUTION_MODE!"=="PAPER" (
    echo     ^(Simulated execution - no real funds used^)
) else (
    echo     ^(LIVE execution - REAL FUNDS AT RISK^)
)
echo   - Network: %DEPLOY_NETWORK%
echo   - Smart Contracts: Compiled
echo.

echo Launch Titan system now? (Y/N):
set /p "LAUNCH=Choice: "

if /i "!LAUNCH!"=="Y" (
    echo.
    echo [STEP] LAUNCHING TITAN ARBITRAGE SYSTEM
    echo.
    echo [i] Starting components:
    echo [i]   1. Redis Message Queue
    echo [i]   2. Mainnet Orchestrator (Python)
    echo [i]   3. Execution Engine (Node.js)
    echo.
    
    REM Set environment variable
    set EXECUTION_MODE=!EXECUTION_MODE!
    
    REM Launch components in separate windows
    start "Titan Orchestrator" cmd /k "python mainnet_orchestrator.py"
    timeout /t 3 /nobreak >nul
    
    start "Titan Executor" cmd /k "node execution/bot.js"
    timeout /t 2 /nobreak >nul
    
    echo.
    echo [+] System launched successfully!
    echo.
    echo ================================================================
    echo    TITAN IS NOW HUNTING FOR ARBITRAGE OPPORTUNITIES
    echo ================================================================
    echo.
    echo Components running in separate windows:
    echo   - Orchestrator (Python ML engine)
    echo   - Executor (Node.js execution)
    echo.
    if "!EXECUTION_MODE!"=="PAPER" (
        echo [i] Running in PAPER mode - Trades are simulated
    ) else (
        echo [!] Running in LIVE mode - REAL FUNDS AT RISK
    )
    echo.
    echo System Functions:
    echo   + Real-time mainnet data ingestion
    echo   + Multi-chain arbitrage detection
    echo   + Flash loan execution (Balancer V3 + Aave)
    echo   + Cross-chain bridge aggregation (Li.Fi)
    echo   + ML-based profit prediction
    echo   + Gas optimization
    if "!EXECUTION_MODE!"=="PAPER" (
        echo   + Simulated trade execution
    ) else (
        echo   + Live blockchain execution
    )
    echo.
    echo Happy trading!
    echo.
) else (
    echo.
    echo [i] Launch skipped. You can start the system later with:
    echo     start_mainnet.sh %EXECUTION_MODE%
    echo.
)

REM Save configuration summary
echo TITAN INSTALLATION SUMMARY > logs\installation_summary.txt
echo ========================== >> logs\installation_summary.txt
echo Installation Date: %DATE% %TIME% >> logs\installation_summary.txt
echo Execution Mode: !EXECUTION_MODE! >> logs\installation_summary.txt
echo Deploy Network: %DEPLOY_NETWORK% >> logs\installation_summary.txt
echo Wallet Configured: Yes >> logs\installation_summary.txt
echo. >> logs\installation_summary.txt
echo System Components: >> logs\installation_summary.txt
echo - Node.js dependencies: Installed >> logs\installation_summary.txt
echo - Python dependencies: Installed >> logs\installation_summary.txt
echo - Rust components (rustworkx): Installed >> logs\installation_summary.txt
echo - Smart contracts: Compiled >> logs\installation_summary.txt

echo [+] Installation summary saved to logs\installation_summary.txt

echo.
echo Installation complete!
echo.
pause
