"""Quick performance test for scraping optimizations"""

import time
from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper

def test_scraping_speed():
    """Test scraping speed for current page jobs"""
    
    print("="*60)
    print("🚀 SELENIUM PERFORMANCE TEST")
    print("="*60)
    print()
    
    # Login
    print("🔑 Logging in...")
    auth = WaterlooWorksAuth()
    auth.login()
    
    # Create scraper
    scraper = WaterlooWorksScraper(auth.driver)
    scraper.go_to_jobs_page()
    
    # Time the scraping (with details - the slowest operation)
    print("\n" + "="*60)
    print("📊 Testing scraping performance with job details...")
    print("="*60)
    print()
    
    start = time.time()
    jobs = scraper.scrape_current_page(include_details=True)
    elapsed = time.time() - start
    
    # Calculate metrics
    num_jobs = len(jobs)
    time_per_job = elapsed / num_jobs if num_jobs > 0 else 0
    
    print()
    print("="*60)
    print("📊 PERFORMANCE RESULTS")
    print("="*60)
    print(f"Total jobs scraped:    {num_jobs}")
    print(f"Total time:            {elapsed:.2f}s ({elapsed/60:.1f}m)")
    print(f"Time per job:          {time_per_job:.2f}s")
    print("="*60)
    print()
    
    # Performance evaluation
    if time_per_job < 1.5:
        print("🏆 EXCELLENT - Scraping is highly optimized!")
        print("   Target achieved: < 1.5s per job")
    elif time_per_job < 2.0:
        print("✅ VERY GOOD - Scraping is well optimized!")
        print("   Phase 1 target achieved: < 2.0s per job")
    elif time_per_job < 3.0:
        print("✓ GOOD - Scraping is reasonably fast")
        print("   Consider Phase 2 optimizations for further improvement")
    elif time_per_job < 4.0:
        print("⚠️  MODERATE - Some optimization has been applied")
        print("   Review wait times and element interactions")
    else:
        print("⚠️  SLOW - More optimizations needed")
        print("   Current performance is below target")
    
    print()
    
    # Comparison with baseline
    baseline_per_job = 5.4  # Original performance
    improvement = ((baseline_per_job - time_per_job) / baseline_per_job) * 100
    
    if improvement > 0:
        print(f"📈 Improvement vs baseline (5.4s/job): {improvement:.1f}% faster")
    else:
        print(f"📉 Performance vs baseline: {abs(improvement):.1f}% slower (unexpected)")
    
    print()
    print("="*60)
    
    # Cleanup
    auth.close()
    
    return {
        "num_jobs": num_jobs,
        "total_time": elapsed,
        "time_per_job": time_per_job,
        "improvement_percent": improvement
    }

if __name__ == "__main__":
    try:
        results = test_scraping_speed()
        
        print()
        print("🎯 Next Steps:")
        if results["time_per_job"] < 2.0:
            print("   ✅ Phase 1 optimizations working well!")
            print("   💡 Consider implementing Phase 2 for even better performance")
        else:
            print("   📋 Review the optimization implementation guide")
            print("   🔍 Check for any errors in the terminal output above")
            print("   ⚙️  Consider adjusting WaitTimes if network is slow")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
