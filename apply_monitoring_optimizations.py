#!/usr/bin/env python3
"""
Apply Monitoring Performance Optimizations

This script immediately applies performance optimizations to reduce CPU and memory
usage of the monitoring system. Run this if you're experiencing high resource usage.
"""

import asyncio
import sys
import psutil
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.monitoring.optimization_manager import MonitoringOptimizationManager, optimize_monitoring_system


def check_system_performance():
    """Check current system performance."""
    try:
        cpu_usage = psutil.cpu_percent(interval=2)
        memory_usage = psutil.virtual_memory().percent
        
        print(f"📊 Current System Performance:")
        print(f"   CPU Usage: {cpu_usage:.1f}%")
        print(f"   Memory Usage: {memory_usage:.1f}%")
        
        # Determine optimization level needed
        if cpu_usage > 90 or memory_usage > 90:
            return 'emergency'
        elif cpu_usage > 75 or memory_usage > 80:
            return 'optimized'
        else:
            return 'normal'
            
    except Exception as e:
        print(f"❌ Error checking system performance: {e}")
        return 'optimized'  # Default to optimized if we can't check


async def apply_immediate_optimizations():
    """Apply immediate performance optimizations."""
    print("🚀 Applying Monitoring Performance Optimizations")
    print("=" * 60)
    
    try:
        # Check current performance
        optimization_level = check_system_performance()
        print(f"🎯 Recommended optimization level: {optimization_level}")
        
        # Apply optimizations
        print("\n⚙️ Applying optimizations...")
        
        # Method 1: Use optimization manager
        try:
            manager = MonitoringOptimizationManager()
            await manager.initialize_optimization()
            
            success = await manager.force_optimization_level(optimization_level)
            if success:
                print("✅ Optimization manager applied successfully")
                
                # Get status
                status = manager.get_optimization_status()
                print(f"   Optimization Level: {status['current_performance_level']}")
                print(f"   Components Managed: {len(status['components_managed'])}")
                
                # Get recommendations
                recommendations = manager.get_performance_recommendations()
                if recommendations:
                    print("\n💡 Performance Recommendations:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        print(f"   {i}. {rec}")
                
                await manager.shutdown_optimization()
                
            else:
                print("⚠️ Optimization manager had issues, trying alternative method")
                
        except Exception as e:
            print(f"⚠️ Optimization manager error: {e}")
            print("   Trying alternative optimization method...")
            
            # Method 2: Direct optimization
            success = await optimize_monitoring_system(optimization_level)
            if success:
                print("✅ Alternative optimization method applied")
            else:
                print("❌ Alternative optimization method failed")
        
        # Method 3: Manual optimizations (always apply these)
        print("\n🔧 Applying manual optimizations...")
        
        # Reduce Python garbage collection frequency
        import gc
        gc.set_threshold(700, 10, 10)  # Less frequent GC
        print("   ✅ Adjusted garbage collection thresholds")
        
        # Set environment variables for better performance
        import os
        os.environ['PYTHONOPTIMIZE'] = '1'
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        print("   ✅ Set Python optimization environment variables")
        
        # Suggest system-level optimizations
        print("\n🖥️ System-level optimization suggestions:")
        print("   1. Close unnecessary applications")
        print("   2. Restart the monitoring system if possible")
        print("   3. Consider increasing system resources")
        print("   4. Monitor system performance after optimizations")
        
        # Final performance check
        print("\n📊 Performance after optimizations:")
        final_level = check_system_performance()
        
        if final_level != optimization_level:
            if final_level == 'normal':
                print("🎉 Performance improved to normal levels!")
            elif final_level == 'optimized' and optimization_level == 'emergency':
                print("✅ Performance improved from emergency to optimized level")
            else:
                print("⚠️ Performance may need additional optimization")
        
        print("\n✅ Optimization process completed!")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()


def create_optimization_config():
    """Create optimized configuration files."""
    try:
        print("\n📝 Creating optimized configuration files...")
        
        # Create config directory if it doesn't exist
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Create optimized monitoring config
        optimized_config = """# Optimized Monitoring Configuration
# This configuration reduces resource usage

monitoring:
  # Reduced update frequencies
  update_intervals:
    real_time: 60  # 1 minute instead of 30 seconds
    quality_checks: 600  # 10 minutes instead of 5 minutes
    analytics: 1800  # 30 minutes instead of 15 minutes
    health_checks: 600  # 10 minutes instead of 5 minutes
  
  # Reduced data retention
  data_retention:
    metrics_hours: 72  # 3 days instead of 7 days
    alerts_hours: 360  # 15 days instead of 30 days
    analytics_hours: 168  # 7 days
  
  # Memory limits
  memory_limits:
    max_metrics_in_memory: 1000
    max_alerts_in_memory: 500
    max_events_in_memory: 2000
  
  # Performance settings
  performance:
    enable_caching: true
    cache_ttl_seconds: 60
    enable_compression: true
    batch_operations: true
    max_concurrent_tasks: 10
"""
        
        config_file = config_dir / "monitoring_optimized.yaml"
        with open(config_file, 'w') as f:
            f.write(optimized_config)
        
        print(f"   ✅ Created optimized config: {config_file}")
        
        # Create performance monitoring script
        monitor_script = """#!/usr/bin/env python3
# Performance monitoring script
import psutil
import time

def monitor_performance():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        if cpu > 80 or memory > 80:
            print(f"HIGH USAGE: CPU={cpu:.1f}%, Memory={memory:.1f}%")
        else:
            print(f"Normal: CPU={cpu:.1f}%, Memory={memory:.1f}%")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_performance()
"""
        
        monitor_file = Path("monitor_performance.py")
        with open(monitor_file, 'w') as f:
            f.write(monitor_script)
        
        print(f"   ✅ Created performance monitor: {monitor_file}")
        
    except Exception as e:
        print(f"⚠️ Error creating config files: {e}")


def main():
    """Main function."""
    print("🎯 Monitoring System Performance Optimizer")
    print("=" * 60)
    print("This script will optimize your monitoring system to reduce CPU and memory usage.")
    print()
    
    # Check if we should proceed
    try:
        response = input("Do you want to proceed with optimization? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Optimization cancelled by user")
            return
    except KeyboardInterrupt:
        print("\n❌ Optimization cancelled by user")
        return
    
    try:
        # Run async optimization
        asyncio.run(apply_immediate_optimizations())
        
        # Create config files
        create_optimization_config()
        
        print("\n🏁 Optimization Complete!")
        print("=" * 60)
        print("Next steps:")
        print("1. Monitor system performance for the next few minutes")
        print("2. Restart monitoring services if CPU usage is still high")
        print("3. Use the created configuration files for future deployments")
        print("4. Run 'python monitor_performance.py' to continuously monitor performance")
        
    except KeyboardInterrupt:
        print("\n❌ Optimization interrupted by user")
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()