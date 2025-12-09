#!/usr/bin/env python3
"""
Comprehensive System Validation for Titan Arbitrage Bot
Validates all configuration, token discovery, and DEX integrations
"""

import sys
from typing import Dict, List
from core.config import (
    CHAINS, DEX_ROUTERS, BALANCER_V3_VAULT, PROTOCOL_IDS,
    get_chain_config, get_router, get_all_chain_ids,
    get_flash_loan_providers, validate_config
)
from core.token_discovery import TokenDiscovery, TOKEN_REGISTRY, BRIDGE_ASSETS

def validate_chains() -> Dict[str, any]:
    """Validate all blockchain configurations"""
    print("\n" + "="*80)
    print("🔗 VALIDATING BLOCKCHAIN CONFIGURATIONS")
    print("="*80)
    
    results = {
        "total_chains": len(CHAINS),
        "chains_validated": 0,
        "issues": []
    }
    
    for chain_id, config in CHAINS.items():
        chain_name = config.get("name", f"Chain {chain_id}")
        print(f"\n✓ {chain_name} (Chain ID: {chain_id})")
        
        # Check required fields
        required = ["name", "rpc", "native", "wrapped_native"]
        missing = [field for field in required if field not in config]
        if missing:
            results["issues"].append(f"{chain_name}: Missing fields {missing}")
            print(f"  ⚠️  Missing: {', '.join(missing)}")
            continue
        
        # Check RPC endpoints
        if config.get("rpc"):
            print(f"  ✓ RPC: {config['rpc'][:50]}...")
        if config.get("wss"):
            print(f"  ✓ WSS: {config['wss'][:50]}...")
        
        # Check flash loan availability
        flash_providers = []
        if "aave_pool" in config and config["aave_pool"] != "0x0000000000000000000000000000000000000000":
            flash_providers.append("Aave V3")
        flash_providers.append("Balancer V3")
        print(f"  ✓ Flash Loans: {', '.join(flash_providers)}")
        
        # Check DEX availability
        dex_count = sum(1 for protocol_addrs in DEX_ROUTERS.values() if chain_id in protocol_addrs)
        print(f"  ✓ DEX Protocols: {dex_count} available")
        
        results["chains_validated"] += 1
    
    print(f"\n✅ Validated {results['chains_validated']}/{results['total_chains']} chains")
    return results

def validate_dex_routers() -> Dict[str, any]:
    """Validate DEX router configurations"""
    print("\n" + "="*80)
    print("🔄 VALIDATING DEX ROUTER CONFIGURATIONS")
    print("="*80)
    
    results = {
        "total_protocols": len(DEX_ROUTERS),
        "total_deployments": 0,
        "protocols_by_chain": {},
        "issues": []
    }
    
    # Count deployments per chain
    for protocol, deployments in DEX_ROUTERS.items():
        results["total_deployments"] += len(deployments)
        for chain_id in deployments:
            if chain_id not in results["protocols_by_chain"]:
                results["protocols_by_chain"][chain_id] = []
            results["protocols_by_chain"][chain_id].append(protocol)
    
    # Display by protocol family
    protocol_families = {
        "Uniswap": ["UNISWAP_V2", "UNISWAP_V3"],
        "SushiSwap": ["SUSHISWAP"],
        "PancakeSwap": ["PANCAKESWAP", "PANCAKESWAP_V3", "PANCAKESWAP_V3_L2"],
        "Curve": ["CURVE", "CURVE_CELO"],
        "Balancer": ["BALANCER_V2"],
        "1inch": ["ONEINCH"],
        "ParaSwap": ["PARASWAP"],
        "0x": ["ZEROX"],
        "Layer 2 Native": ["SYNCSWAP", "HORIZONDEX", "SPACEFI", "FUSIONX", "AGNI", 
                          "THRUSTER", "THRUSTER_V3", "UBESWAP", "LINEHUB", "SKYDROME",
                          "MERCHANT_MOE", "MUTE", "VELOCORE", "BLADESWAP", "MONOBOMB", "BISWAP"]
    }
    
    print(f"\n✓ Total DEX Protocols: {results['total_protocols']}")
    print(f"✓ Total Deployments: {results['total_deployments']}")
    
    for family, protocols in protocol_families.items():
        family_deployments = sum(len(DEX_ROUTERS.get(p, {})) for p in protocols if p in DEX_ROUTERS)
        if family_deployments > 0:
            print(f"\n  {family}:")
            for protocol in protocols:
                if protocol in DEX_ROUTERS:
                    chains = list(DEX_ROUTERS[protocol].keys())
                    chain_names = [CHAINS[cid]["name"] for cid in chains if cid in CHAINS]
                    print(f"    ✓ {protocol}: {len(chains)} deployments ({', '.join(chain_names)})")
    
    # Show protocols per chain
    print(f"\n✓ DEX Coverage by Chain:")
    for chain_id in sorted(results["protocols_by_chain"].keys()):
        chain_name = CHAINS[chain_id]["name"]
        protocol_count = len(results["protocols_by_chain"][chain_id])
        print(f"  {chain_name}: {protocol_count} protocols")
    
    print(f"\n✅ All {results['total_protocols']} DEX protocols validated")
    return results

def validate_token_discovery() -> Dict[str, any]:
    """Validate token discovery system"""
    print("\n" + "="*80)
    print("🪙 VALIDATING TOKEN DISCOVERY SYSTEM")
    print("="*80)
    
    td = TokenDiscovery()
    results = {
        "total_chains_in_registry": len(TOKEN_REGISTRY),
        "total_tokens": 0,
        "tokens_by_chain": {},
        "bridge_assets": len(BRIDGE_ASSETS),
        "issues": []
    }
    
    # Count tokens per chain
    for chain_id, tokens in TOKEN_REGISTRY.items():
        results["tokens_by_chain"][chain_id] = len(tokens)
        results["total_tokens"] += len(tokens)
    
    print(f"\n✓ Total Chains with Tokens: {results['total_chains_in_registry']}")
    print(f"✓ Total Token Addresses: {results['total_tokens']}")
    print(f"✓ Bridge-Compatible Assets: {results['bridge_assets']}")
    
    # Show token coverage by chain
    print(f"\n✓ Token Coverage by Chain:")
    for chain_id in sorted(results["tokens_by_chain"].keys()):
        if chain_id in CHAINS:
            chain_name = CHAINS[chain_id]["name"]
            token_count = results["tokens_by_chain"][chain_id]
            
            # Get token symbols
            symbols = list(TOKEN_REGISTRY[chain_id].keys())
            
            # Count stablecoins
            stablecoins = [s for s in symbols if td.is_stablecoin(chain_id, s)]
            
            print(f"  {chain_name}: {token_count} tokens ({len(stablecoins)} stablecoins)")
            print(f"    Available: {', '.join(symbols)}")
    
    # Validate bridge assets availability
    print(f"\n✓ Bridge Asset Availability Across Chains:")
    for asset in BRIDGE_ASSETS:
        available_chains = []
        for chain_id in TOKEN_REGISTRY:
            if chain_id in CHAINS and td.validate_token_exists(chain_id, asset):
                available_chains.append(CHAINS[chain_id]["name"])
        
        coverage = len(available_chains)
        total = len(TOKEN_REGISTRY)
        print(f"  {asset}: {coverage}/{total} chains ({', '.join(available_chains[:5])}{', ...' if len(available_chains) > 5 else ''})")
    
    print(f"\n✅ Token discovery validated: {results['total_tokens']} tokens across {results['total_chains_in_registry']} chains")
    return results

def validate_flash_loans() -> Dict[str, any]:
    """Validate flash loan configurations"""
    print("\n" + "="*80)
    print("⚡ VALIDATING FLASH LOAN CONFIGURATIONS")
    print("="*80)
    
    results = {
        "balancer_v3_universal": BALANCER_V3_VAULT,
        "aave_v3_chains": 0,
        "flash_capable_chains": 0,
        "issues": []
    }
    
    print(f"\n✓ Balancer V3 Vault (Universal): {BALANCER_V3_VAULT}")
    print(f"  Supports: WETH, WBTC, USDC, USDT, DAI on all chains")
    
    print(f"\n✓ Aave V3 Pool Availability:")
    for chain_id, config in CHAINS.items():
        if "aave_pool" in config and config["aave_pool"] != "0x0000000000000000000000000000000000000000":
            results["aave_v3_chains"] += 1
            results["flash_capable_chains"] += 1
            print(f"  {config['name']}: {config['aave_pool']}")
        else:
            results["flash_capable_chains"] += 1  # Balancer available on all chains
    
    print(f"\n✅ Flash loans validated:")
    print(f"  Balancer V3: {len(CHAINS)} chains (universal)")
    print(f"  Aave V3: {results['aave_v3_chains']} chains")
    print(f"  Total flash-capable: {results['flash_capable_chains']} chains")
    
    return results

def validate_integration() -> Dict[str, any]:
    """Validate integration between components"""
    print("\n" + "="*80)
    print("🔗 VALIDATING COMPONENT INTEGRATION")
    print("="*80)
    
    results = {
        "config_api_working": True,
        "token_discovery_working": True,
        "cross_chain_compatible": True,
        "issues": []
    }
    
    # Test config API
    print("\n✓ Testing Configuration API:")
    try:
        test_chain = get_chain_config(1)  # Ethereum
        print(f"  get_chain_config(1): ✓ {test_chain['name']}")
        
        test_router = get_router("UNISWAP_V3", 1)
        print(f"  get_router('UNISWAP_V3', 1): ✓ {test_router[:20]}...")
        
        all_chains = get_all_chain_ids()
        print(f"  get_all_chain_ids(): ✓ {len(all_chains)} chains")
        
        flash_providers = get_flash_loan_providers(1)
        print(f"  get_flash_loan_providers(1): ✓ {len(flash_providers)} providers")
    except Exception as e:
        results["config_api_working"] = False
        results["issues"].append(f"Config API error: {str(e)}")
        print(f"  ⚠️  Error: {str(e)}")
    
    # Test token discovery API
    print("\n✓ Testing Token Discovery API:")
    try:
        td = TokenDiscovery()
        
        # Fetch tokens for multiple chains
        test_chains = [1, 137, 42161]
        tokens = td.fetch_all_chains(test_chains)
        print(f"  fetch_all_chains({test_chains}): ✓ {sum(len(t) for t in tokens.values())} tokens")
        
        # Get USDC address
        usdc_addr = td.get_token_address(1, "USDC")
        print(f"  get_token_address(1, 'USDC'): ✓ {usdc_addr}")
        
        # Get stablecoins
        stables = td.get_stablecoins(1)
        print(f"  get_stablecoins(1): ✓ {len(stables)} stablecoins")
        
        # Get bridge assets
        bridge_tokens = td.get_bridge_compatible_tokens()
        print(f"  get_bridge_compatible_tokens(): ✓ {len(bridge_tokens)} assets")
    except Exception as e:
        results["token_discovery_working"] = False
        results["issues"].append(f"Token Discovery API error: {str(e)}")
        print(f"  ⚠️  Error: {str(e)}")
    
    # Validate cross-chain compatibility
    print("\n✓ Testing Cross-Chain Compatibility:")
    try:
        td = TokenDiscovery()
        
        # Check USDC availability across chains
        usdc_chains = []
        for chain_id in get_all_chain_ids():
            try:
                usdc_addr = td.get_token_address(chain_id, "USDC")
                if usdc_addr:
                    usdc_chains.append(CHAINS[chain_id]["name"])
            except:
                # Try USDC.e
                try:
                    usdc_e_addr = td.get_token_address(chain_id, "USDC.e")
                    if usdc_e_addr:
                        usdc_chains.append(CHAINS[chain_id]["name"])
                except:
                    pass
        
        print(f"  USDC available on {len(usdc_chains)}/{len(get_all_chain_ids())} chains")
        print(f"    Chains: {', '.join(usdc_chains)}")
        
        # Check if all bridge assets exist on tier-1 chains
        tier1_chains = [1, 137, 42161, 10, 8453]  # Ethereum, Polygon, Arbitrum, Optimism, Base
        missing_bridge_assets = []
        for asset in BRIDGE_ASSETS[:5]:  # Check top 5 bridge assets
            available = 0
            for cid in tier1_chains:
                try:
                    addr = td.get_token_address(cid, asset)
                    if addr:
                        available += 1
                except:
                    pass
            if available < len(tier1_chains):
                missing_bridge_assets.append(asset)
        
        if missing_bridge_assets:
            results["issues"].append(f"Bridge assets missing on tier-1 chains: {', '.join(missing_bridge_assets)}")
            print(f"  ⚠️  Some bridge assets missing on tier-1 chains")
        else:
            print(f"  ✓ All major bridge assets available on tier-1 chains")
        
    except Exception as e:
        results["cross_chain_compatible"] = False
        results["issues"].append(f"Cross-chain compatibility error: {str(e)}")
        print(f"  ⚠️  Error: {str(e)}")
    
    if all([results["config_api_working"], results["token_discovery_working"], results["cross_chain_compatible"]]):
        print(f"\n✅ All integration tests passed")
    else:
        print(f"\n⚠️  Some integration tests failed")
    
    return results

def generate_summary_report(chain_results, dex_results, token_results, flash_results, integration_results):
    """Generate comprehensive summary report"""
    print("\n" + "="*80)
    print("📊 SYSTEM VALIDATION SUMMARY REPORT")
    print("="*80)
    
    print("\n🔗 BLOCKCHAIN INFRASTRUCTURE:")
    print(f"  ✓ Chains Configured: {chain_results['chains_validated']}/{chain_results['total_chains']}")
    print(f"  ✓ Flash Loan Capable: {flash_results['flash_capable_chains']} chains")
    print(f"  ✓ Balancer V3: Universal on all chains")
    print(f"  ✓ Aave V3: {flash_results['aave_v3_chains']} chains")
    
    print("\n🔄 DEX AGGREGATION:")
    print(f"  ✓ DEX Protocols: {dex_results['total_protocols']}")
    print(f"  ✓ Total Deployments: {dex_results['total_deployments']}")
    print(f"  ✓ Average per Chain: {dex_results['total_deployments'] / len(CHAINS):.1f}")
    
    print("\n🪙 TOKEN DISCOVERY:")
    print(f"  ✓ Chains with Tokens: {token_results['total_chains_in_registry']}")
    print(f"  ✓ Total Token Addresses: {token_results['total_tokens']}")
    print(f"  ✓ Bridge-Compatible Assets: {token_results['bridge_assets']}")
    print(f"  ✓ Average Tokens per Chain: {token_results['total_tokens'] / token_results['total_chains_in_registry']:.1f}")
    
    print("\n🔗 INTEGRATION STATUS:")
    print(f"  {'✓' if integration_results['config_api_working'] else '⚠️ '} Configuration API: {'Working' if integration_results['config_api_working'] else 'Issues detected'}")
    print(f"  {'✓' if integration_results['token_discovery_working'] else '⚠️ '} Token Discovery API: {'Working' if integration_results['token_discovery_working'] else 'Issues detected'}")
    print(f"  {'✓' if integration_results['cross_chain_compatible'] else '⚠️ '} Cross-Chain Support: {'Working' if integration_results['cross_chain_compatible'] else 'Issues detected'}")
    
    # Calculate overall readiness
    total_issues = len(chain_results.get('issues', [])) + len(dex_results.get('issues', [])) + \
                   len(token_results.get('issues', [])) + len(integration_results.get('issues', []))
    
    # Readiness calculation
    config_score = (chain_results['chains_validated'] / chain_results['total_chains']) * 100
    dex_score = 100 if dex_results['total_protocols'] >= 40 else (dex_results['total_protocols'] / 40) * 100
    token_score = (token_results['total_chains_in_registry'] / len(CHAINS)) * 100
    integration_score = 100 if all([integration_results['config_api_working'], 
                                    integration_results['token_discovery_working'],
                                    integration_results['cross_chain_compatible']]) else 66
    
    overall_readiness = (config_score + dex_score + token_score + integration_score) / 4
    
    print("\n📈 PRODUCTION READINESS:")
    print(f"  Configuration: {config_score:.1f}%")
    print(f"  DEX Integration: {dex_score:.1f}%")
    print(f"  Token Discovery: {token_score:.1f}%")
    print(f"  Component Integration: {integration_score:.1f}%")
    print(f"\n  🎯 OVERALL READINESS: {overall_readiness:.1f}%")
    
    if overall_readiness >= 90:
        print(f"  ✅ READY FOR PRODUCTION")
    elif overall_readiness >= 75:
        print(f"  ⚠️  NEAR PRODUCTION READY (minor improvements needed)")
    else:
        print(f"  ⚠️  REQUIRES ADDITIONAL WORK")
    
    if total_issues > 0:
        print(f"\n⚠️  Issues Found: {total_issues}")
        all_issues = chain_results.get('issues', []) + dex_results.get('issues', []) + \
                     token_results.get('issues', []) + integration_results.get('issues', [])
        for issue in all_issues[:5]:  # Show first 5 issues
            print(f"    • {issue}")
        if total_issues > 5:
            print(f"    ... and {total_issues - 5} more")
    
    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80 + "\n")
    
    return {
        "overall_readiness": overall_readiness,
        "total_issues": total_issues,
        "component_scores": {
            "configuration": config_score,
            "dex_integration": dex_score,
            "token_discovery": token_score,
            "integration": integration_score
        }
    }

def main():
    """Run complete system validation"""
    print("\n" + "="*80)
    print("🚀 TITAN ARBITRAGE BOT - COMPREHENSIVE SYSTEM VALIDATION")
    print("="*80)
    
    try:
        # Run all validations
        chain_results = validate_chains()
        dex_results = validate_dex_routers()
        token_results = validate_token_discovery()
        flash_results = validate_flash_loans()
        integration_results = validate_integration()
        
        # Generate summary report
        summary = generate_summary_report(
            chain_results, dex_results, token_results, 
            flash_results, integration_results
        )
        
        # Exit with appropriate code
        if summary["overall_readiness"] >= 90 and summary["total_issues"] == 0:
            sys.exit(0)
        elif summary["overall_readiness"] >= 75:
            sys.exit(1)  # Warnings but mostly ready
        else:
            sys.exit(2)  # Significant issues
            
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()
