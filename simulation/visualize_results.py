#!/usr/bin/env python3
"""
Titan Simulation Results Visualizer
====================================

Creates visual charts and graphs from simulation results:
- Daily profit trends
- Success rate over time
- Cumulative profit
- Opportunity distribution
- Feature usage analysis

Requires matplotlib and seaborn for visualization.
"""

import os
import sys
import pandas as pd
import json
from datetime import datetime

# Optional imports for visualization
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("⚠️  Visualization libraries not available.")
    print("Install with: pip install matplotlib seaborn")

def load_simulation_data(results_dir='data/simulation_results'):
    """Load all simulation result files"""
    daily_metrics = pd.read_csv(f'{results_dir}/daily_metrics.csv')
    
    with open(f'{results_dir}/summary.json', 'r') as f:
        summary = json.load(f)
    
    # Optional: Load opportunities if needed
    try:
        opportunities = pd.read_csv(f'{results_dir}/opportunities.csv')
    except:
        opportunities = None
    
    return daily_metrics, summary, opportunities


def create_profit_trend_chart(daily_metrics, output_file='data/simulation_results/profit_trend.png'):
    """Create daily profit trend chart"""
    if not VISUALIZATION_AVAILABLE:
        print("Cannot create charts - visualization libraries not installed")
        return
    
    plt.figure(figsize=(14, 6))
    
    # Filter out zero days
    data = daily_metrics[daily_metrics['opportunities_found'] > 0].copy()
    
    if len(data) == 0:
        print("No data to visualize")
        return
    
    # Plot daily profit
    plt.subplot(1, 2, 1)
    plt.plot(data.index, data['total_profit_usd'], marker='o', linewidth=2, markersize=4)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('Daily Profit Trend', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Profit (USD)')
    plt.grid(True, alpha=0.3)
    
    # Plot cumulative profit
    plt.subplot(1, 2, 2)
    cumulative_profit = data['total_profit_usd'].cumsum()
    plt.plot(data.index, cumulative_profit, marker='o', linewidth=2, markersize=4, color='green')
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('Cumulative Profit', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Cumulative Profit (USD)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved profit trend chart: {output_file}")
    plt.close()


def create_success_rate_chart(daily_metrics, output_file='data/simulation_results/success_rate.png'):
    """Create success rate over time chart"""
    if not VISUALIZATION_AVAILABLE:
        return
    
    data = daily_metrics[daily_metrics['opportunities_found'] > 0].copy()
    
    if len(data) == 0:
        return
    
    plt.figure(figsize=(14, 6))
    
    # Plot success rate
    plt.subplot(1, 2, 1)
    plt.plot(data.index, data['success_rate'] * 100, marker='o', linewidth=2, markersize=4, color='blue')
    plt.axhline(y=85, color='g', linestyle='--', alpha=0.5, label='Target: 85%')
    plt.title('Success Rate Over Time', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Success Rate (%)')
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot executed trades
    plt.subplot(1, 2, 2)
    plt.bar(data.index, data['opportunities_executed'], alpha=0.7, color='orange')
    plt.title('Executed Trades Per Day', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Number of Trades')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved success rate chart: {output_file}")
    plt.close()


def create_gas_analysis_chart(daily_metrics, output_file='data/simulation_results/gas_analysis.png'):
    """Create gas price and cost analysis chart"""
    if not VISUALIZATION_AVAILABLE:
        return
    
    data = daily_metrics[daily_metrics['opportunities_found'] > 0].copy()
    
    if len(data) == 0:
        return
    
    plt.figure(figsize=(14, 6))
    
    # Plot gas prices
    plt.subplot(1, 2, 1)
    plt.plot(data.index, data['avg_gas_price_gwei'], marker='o', linewidth=2, markersize=4, color='red')
    plt.title('Average Gas Price Over Time', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Gas Price (Gwei)')
    plt.grid(True, alpha=0.3)
    
    # Plot gas costs
    plt.subplot(1, 2, 2)
    plt.bar(data.index, data['total_gas_cost_usd'], alpha=0.7, color='purple')
    plt.title('Daily Gas Costs', fontsize=14, fontweight='bold')
    plt.xlabel('Day')
    plt.ylabel('Gas Cost (USD)')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved gas analysis chart: {output_file}")
    plt.close()


def create_summary_dashboard(daily_metrics, summary, output_file='data/simulation_results/dashboard.png'):
    """Create comprehensive dashboard with key metrics"""
    if not VISUALIZATION_AVAILABLE:
        return
    
    data = daily_metrics[daily_metrics['opportunities_found'] > 0].copy()
    
    if len(data) == 0:
        return
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Cumulative Profit
    ax1 = fig.add_subplot(gs[0, :2])
    cumulative_profit = data['total_profit_usd'].cumsum()
    ax1.plot(data.index, cumulative_profit, linewidth=3, color='green')
    ax1.fill_between(data.index, cumulative_profit, alpha=0.3, color='green')
    ax1.set_title('Cumulative Profit', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('USD')
    ax1.grid(True, alpha=0.3)
    
    # 2. Summary Stats
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')
    stats_text = f"""
SIMULATION SUMMARY

Total Days: {len(data)}
Opportunities: {summary['total_opportunities_found']:,}
Executed: {summary['total_opportunities_executed']:,}
Success Rate: {summary['overall_success_rate']*100:.1f}%

Total Profit: ${summary['total_profit_usd']:,.2f}
Gas Costs: ${summary['total_gas_cost_usd']:,.2f}
Net Profit: ${summary['net_profit_usd']:,.2f}

Avg Daily: ${summary['average_daily_profit']:,.2f}
Avg/Trade: ${summary['average_profit_per_trade']:,.2f}
"""
    ax2.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # 3. Success Rate
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(data.index, data['success_rate'] * 100, linewidth=2, color='blue')
    ax3.axhline(y=85, color='g', linestyle='--', alpha=0.5)
    ax3.set_title('Success Rate (%)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Day')
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3)
    
    # 4. Daily Trades
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.bar(data.index, data['opportunities_executed'], alpha=0.7, color='orange')
    ax4.set_title('Daily Executed Trades', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Day')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Gas Prices
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.plot(data.index, data['avg_gas_price_gwei'], linewidth=2, color='red')
    ax5.set_title('Gas Price (Gwei)', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Day')
    ax5.grid(True, alpha=0.3)
    
    # 6. Profit Distribution
    ax6 = fig.add_subplot(gs[2, :])
    ax6.bar(data.index, data['total_profit_usd'], alpha=0.7, 
            color=['green' if x > 0 else 'red' for x in data['total_profit_usd']])
    ax6.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax6.set_title('Daily Profit Distribution', fontsize=12, fontweight='bold')
    ax6.set_xlabel('Day')
    ax6.set_ylabel('Profit (USD)')
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Titan 90-Day Simulation Dashboard', fontsize=16, fontweight='bold')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved dashboard: {output_file}")
    plt.close()


def generate_text_report(daily_metrics, summary, output_file='data/simulation_results/text_report.txt'):
    """Generate text-based analysis report"""
    data = daily_metrics[daily_metrics['opportunities_found'] > 0].copy()
    
    report = []
    report.append("=" * 70)
    report.append("TITAN 90-DAY SIMULATION - DETAILED ANALYSIS REPORT")
    report.append("=" * 70)
    report.append("")
    
    # Overall Summary
    report.append("OVERALL SUMMARY")
    report.append("-" * 70)
    report.append(f"Simulation Period: {summary['simulation_period']}")
    report.append(f"Active Trading Days: {len(data)}")
    report.append(f"Total Opportunities Found: {summary['total_opportunities_found']:,}")
    report.append(f"Total Opportunities Executed: {summary['total_opportunities_executed']:,}")
    report.append(f"Execution Rate: {(summary['total_opportunities_executed']/summary['total_opportunities_found']*100):.1f}%")
    report.append("")
    
    # Performance Metrics
    report.append("PERFORMANCE METRICS")
    report.append("-" * 70)
    report.append(f"Successful Trades: {summary['total_successful_trades']:,}")
    report.append(f"Failed Trades: {summary['total_failed_trades']:,}")
    report.append(f"Overall Success Rate: {summary['overall_success_rate']*100:.1f}%")
    report.append("")
    
    # Financial Summary
    report.append("FINANCIAL SUMMARY")
    report.append("-" * 70)
    report.append(f"Total Profit: ${summary['total_profit_usd']:,.2f}")
    report.append(f"Total Gas Costs: ${summary['total_gas_cost_usd']:,.2f}")
    report.append(f"Net Profit: ${summary['net_profit_usd']:,.2f}")
    report.append(f"Average Daily Profit: ${summary['average_daily_profit']:,.2f}")
    report.append(f"Average Profit Per Trade: ${summary['average_profit_per_trade']:,.2f}")
    report.append("")
    
    # Best/Worst Days
    if len(data) > 0:
        best_day = data.loc[data['total_profit_usd'].idxmax()]
        worst_day = data.loc[data['total_profit_usd'].idxmin()]
        
        report.append("BEST & WORST DAYS")
        report.append("-" * 70)
        report.append(f"Best Day: {best_day['date']}")
        report.append(f"  Profit: ${best_day['total_profit_usd']:,.2f}")
        report.append(f"  Trades: {int(best_day['opportunities_executed'])}")
        report.append(f"  Success Rate: {best_day['success_rate']*100:.1f}%")
        report.append("")
        report.append(f"Worst Day: {worst_day['date']}")
        report.append(f"  Profit: ${worst_day['total_profit_usd']:,.2f}")
        report.append(f"  Trades: {int(worst_day['opportunities_executed'])}")
        report.append(f"  Success Rate: {worst_day['success_rate']*100:.1f}%")
        report.append("")
    
    # Statistical Analysis
    if len(data) > 0:
        report.append("STATISTICAL ANALYSIS")
        report.append("-" * 70)
        report.append(f"Average Opportunities/Day: {data['opportunities_found'].mean():.1f}")
        report.append(f"Average Executions/Day: {data['opportunities_executed'].mean():.1f}")
        report.append(f"Average Success Rate: {data['success_rate'].mean()*100:.1f}%")
        report.append(f"Average Gas Price: {data['avg_gas_price_gwei'].mean():.2f} Gwei")
        report.append(f"Profit Std Dev: ${data['total_profit_usd'].std():,.2f}")
        report.append("")
    
    # Features Used
    report.append("FEATURES ENABLED")
    report.append("-" * 70)
    features = summary.get('features_enabled', {})
    for feature, enabled in features.items():
        status = "✓" if enabled else "✗"
        report.append(f"{status} {feature.replace('_', ' ').title()}")
    report.append("")
    
    report.append("=" * 70)
    report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    
    # Save report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Saved text report: {output_file}")
    
    # Also print to console
    print("\n" + '\n'.join(report))


def main():
    """Main visualization function"""
    print("=" * 70)
    print("📊 TITAN SIMULATION RESULTS VISUALIZATION")
    print("=" * 70)
    print()
    
    # Load data
    try:
        daily_metrics, summary, opportunities = load_simulation_data()
        print(f"✅ Loaded simulation data: {len(daily_metrics)} days")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("   Make sure you've run the simulation first:")
        print("   python run_90day_simulation.py --example-data")
        return 1
    
    # Generate text report (always available)
    generate_text_report(daily_metrics, summary)
    
    # Generate charts if libraries available
    if VISUALIZATION_AVAILABLE:
        print("\n📈 Generating charts...")
        create_profit_trend_chart(daily_metrics)
        create_success_rate_chart(daily_metrics)
        create_gas_analysis_chart(daily_metrics)
        create_summary_dashboard(daily_metrics, summary)
        print("\n✅ All visualizations generated!")
    else:
        print("\n⚠️  Chart generation skipped (matplotlib/seaborn not installed)")
        print("   Install with: pip install matplotlib seaborn")
    
    print("\n" + "=" * 70)
    print("📁 View results in data/simulation_results/")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
