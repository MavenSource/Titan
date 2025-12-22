# Shared Integration Layer

This directory serves as the integration point between on-chain and off-chain components.

## Structure

- `signals/` - IPC directory for brain → executor communication
  - `outgoing/` - New arbitrage signals from the brain
  - `processed/` - Completed or archived signals
- `abi/` - Generated contract ABIs (copied from onchain/artifacts)
- `config/` - Shared configuration files
  - `paths.json` - Centralized path configuration

## Signal Flow

1. Python brain detects arbitrage opportunity
2. Brain writes signal JSON to `signals/outgoing/`
3. JavaScript executor polls `signals/outgoing/`
4. Executor picks up signal, executes trade
5. Executor moves signal to `signals/processed/`

## ABI Management

Contract ABIs are copied from `../onchain/artifacts/` during the build process. The CI/CD pipeline automatically syncs these files.
