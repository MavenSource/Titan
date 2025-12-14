#!/bin/bash
# ==============================================================================
# Test Suite for install_and_run_titan.sh
# ==============================================================================
# Validates that the installation script is properly structured and functional

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Installation Script Test Suite${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

test_count=0
pass_count=0

run_test() {
    local test_name="$1"
    shift
    
    test_count=$((test_count + 1))
    echo -n "Test $test_count: $test_name... "
    
    # Execute command directly without eval for safety
    if "$@" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        pass_count=$((pass_count + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        return 1
    fi
}

# Test 1: Script exists and is executable
run_test "Script exists and is executable" \
    test -x install_and_run_titan.sh

# Test 2: Bash syntax is valid
run_test "Bash syntax is valid" \
    bash -n install_and_run_titan.sh

# Test 3: Help flag works
run_test "Help flag works" \
    sh -c "./install_and_run_titan.sh --help | grep -q 'Usage:'"

# Test 4: Script has all required functions
run_test "Script contains print_banner function" \
    grep -q 'print_banner()' install_and_run_titan.sh

run_test "Script contains print_section function" \
    grep -q 'print_section()' install_and_run_titan.sh

run_test "Script contains command_exists function" \
    grep -q 'command_exists()' install_and_run_titan.sh

# Test 5: Script has all installation steps
run_test "Script has step 1 (Prerequisites)" \
    grep -q 'STEP 1/10: CHECKING SYSTEM PREREQUISITES' install_and_run_titan.sh

run_test "Script has step 2 (Node.js deps)" \
    grep -q 'STEP 2/10: INSTALLING NODE.JS DEPENDENCIES' install_and_run_titan.sh

run_test "Script has step 3 (Python/Rust)" \
    grep -q 'STEP 3/10: INSTALLING PYTHON DEPENDENCIES & RUST COMPONENTS' install_and_run_titan.sh

run_test "Script has step 4 (Redis)" \
    grep -q 'STEP 4/10: SETTING UP REDIS' install_and_run_titan.sh

run_test "Script has step 5 (Contracts)" \
    grep -q 'STEP 5/10: COMPILING SMART CONTRACTS' install_and_run_titan.sh

run_test "Script has step 6 (Environment)" \
    grep -q 'STEP 6/10: CONFIGURING ENVIRONMENT' install_and_run_titan.sh

run_test "Script has step 7 (Data dirs)" \
    grep -q 'STEP 7/10: CREATING DATA DIRECTORIES' install_and_run_titan.sh

run_test "Script has step 8 (Deploy)" \
    grep -q 'STEP 8/10: DEPLOYING SMART CONTRACTS' install_and_run_titan.sh

run_test "Script has step 9 (Audit)" \
    grep -q 'STEP 9/10: RUNNING SYSTEM AUDIT' install_and_run_titan.sh

run_test "Script has step 10 (Launch)" \
    grep -q 'STEP 10/10: SYSTEM READY - LAUNCHING TITAN' install_and_run_titan.sh

# Test 6: Script handles all command-line options
run_test "Script accepts --wallet-key option" \
    grep -q 'wallet-key)' install_and_run_titan.sh

run_test "Script accepts --wallet-address option" \
    grep -q 'wallet-address)' install_and_run_titan.sh

run_test "Script accepts --mode option" \
    grep -q 'mode)' install_and_run_titan.sh

run_test "Script accepts --network option" \
    grep -q 'network)' install_and_run_titan.sh

run_test "Script accepts --skip-redis option" \
    grep -q 'skip-redis)' install_and_run_titan.sh

# Test 7: Script has proper error handling
run_test "Script has 'set -e' for error exit" \
    grep -q '^set -e' install_and_run_titan.sh

run_test "Script validates private key format" \
    grep -q 'Invalid private key format' install_and_run_titan.sh

# Test 8: Windows batch file exists
run_test "Windows batch file exists" \
    test -f install_and_run_titan.bat

# Test 9: Documentation exists
run_test "Full installation guide exists" \
    test -f FULL_INSTALLATION_GUIDE.md

run_test "Installation guide references script" \
    grep -q 'install_and_run_titan.sh' FULL_INSTALLATION_GUIDE.md

# Test 10: README references the installation script
run_test "README references full installation script" \
    grep -q 'install_and_run_titan.sh' README.md

run_test "README references full installation guide" \
    grep -q 'FULL_INSTALLATION_GUIDE.md' README.md

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "Test Results: ${GREEN}$pass_count${NC}/${BLUE}$test_count${NC} passed"

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${BLUE}================================${NC}"
    exit 0
else
    failed_count=$((test_count - pass_count))
    echo -e "${RED}$failed_count test(s) failed${NC}"
    echo -e "${BLUE}================================${NC}"
    exit 1
fi
