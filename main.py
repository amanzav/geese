"""
Waterloo Works Automator - Main Pipeline
Scrapes jobs, analyzes matches, and shows best opportunities
"""

import json
import os
import getpass
from datetime import datetime
from typing import List, Dict

from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper
from modules.matcher import ResumeMatcher, load_config


class JobAnalyzer:
    """Main pipeline for scraping and analyzing WaterlooWorks jobs"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize analyzer with configuration"""
        self.config = load_config(config_path)
        self.matcher = ResumeMatcher(config_path)
        print("✅ Job Analyzer initialized\n")
    
    def run_full_pipeline(self, detailed: bool = True, force_rematch: bool = False) -> List[Dict]:
        """
        Run complete pipeline: scrape → match → filter → save
        
        Args:
            detailed: Whether to scrape detailed job info (slower but better)
            force_rematch: If True, ignore cached matches and recalculate all
        
        Returns:
            List of analyzed jobs sorted by fit score
        """
        print("=" * 70)
        print("🚀 WATERLOO WORKS JOB ANALYZER")
        print("=" * 70)
        print()
        
        # Step 1: Scrape jobs
        print("📥 Step 1: Scraping jobs from WaterlooWorks...")
        jobs = self._scrape_jobs(detailed=detailed)
        
        if not jobs:
            print("❌ No jobs found. Exiting.")
            return []
        
        print(f"✅ Found {len(jobs)} jobs\n")
        
        # Step 2: Analyze matches
        print("🔍 Step 2: Analyzing job matches...")
        if force_rematch:
            print("⚠️  Force rematch enabled - ignoring cache")
        results = self.matcher.batch_analyze(jobs, force_rematch=force_rematch)
        print(f"✅ Analyzed {len(results)} jobs\n")
        
        # Step 3: Filter results
        print("🎯 Step 3: Applying filters...")
        filtered_results = self._apply_filters(results)
        print(f"✅ {len(filtered_results)} jobs after filtering\n")
        
        # Step 4: Save results
        print("💾 Step 4: Saving results...")
        self._save_results(filtered_results)
        print()
        
        # Step 5: Show summary
        self._show_summary(filtered_results)
        
        return filtered_results
    
    def _scrape_jobs(self, detailed: bool = True) -> List[Dict]:
        """Scrape jobs from WaterlooWorks with incremental saving"""
        try:
            # Load existing jobs from cache
            os.makedirs("data", exist_ok=True)
            cache_path = "data/jobs_scraped.json"
            existing_jobs = {}
            
            if os.path.exists(cache_path):
                print("📂 Loading existing jobs from cache...")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    # Build a dict for fast lookup by job ID
                    existing_jobs = {job['id']: job for job in cached if 'id' in job}
                    print(f"   Found {len(existing_jobs)} cached jobs\n")
            
            # Get credentials
            print("🔐 Enter your WaterlooWorks credentials")
            username = input("Username (UW email): ").strip()
            password = getpass.getpass("Password: ")
            print()
            
            # Login
            auth = WaterlooWorksAuth(username, password)
            auth.login()
            
            # Scrape with incremental saving
            scraper = WaterlooWorksScraper(auth.driver)
            scraper.go_to_jobs_page()
            
            # Pass existing jobs and save callback
            def save_callback(jobs):
                """Called after each page to save progress"""
                normalized = self._normalize_job_data(jobs)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(normalized, f, indent=2, ensure_ascii=False)
            
            jobs = scraper.scrape_all_jobs(
                include_details=detailed,
                existing_jobs=existing_jobs,
                save_callback=save_callback,
                save_every=5  # Save after every 5 new jobs (adjust as needed)
            )
            
            # Close browser
            auth.close()
            
            # Final normalization and save
            jobs = self._normalize_job_data(jobs)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Total jobs in cache: {len(jobs)}")
            print(f"   Newly scraped: {len([j for j in jobs if j.get('id') not in existing_jobs])}")
            print(f"   From cache: {len(existing_jobs)}\n")
            
            return jobs
        
        except Exception as e:
            print(f"❌ Error scraping jobs: {e}")
            
            # Try to use cached data
            if os.path.exists("data/jobs_scraped.json"):
                print("📂 Using cached jobs from previous run...")
                with open("data/jobs_scraped.json", 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return []
    
    def _normalize_job_data(self, jobs: List[Dict]) -> List[Dict]:
        """Normalize job data format for consistency"""
        # No normalization needed anymore - scraper already uses 'location'
        return jobs
    
    def _apply_filters(self, results: List[Dict]) -> List[Dict]:
        """Apply location, keyword, and company filters"""
        filtered = []
        
        preferred_locations = self.config.get("preferred_locations", [])
        keywords = self.config.get("keywords_to_match", [])
        avoid_companies = self.config.get("companies_to_avoid", [])
        min_score = self.config.get("matcher", {}).get("min_match_score", 0)
        
        for result in results:
            job = result["job"]
            match = result["match"]
            
            # Filter by minimum score
            if match["fit_score"] < min_score:
                continue
            
            # Filter by location
            if preferred_locations:
                job_location = job.get("location", "").lower()
                if not any(loc.lower() in job_location for loc in preferred_locations):
                    continue
            
            # Filter by keywords (if any match)
            if keywords:
                # Search across all text fields
                job_text_parts = []
                for field in ['title', 'summary', 'responsibilities', 'skills', 'employment_location_arrangement', 'work_term_duration']:
                    if job.get(field) and job[field] != 'N/A':
                        job_text_parts.append(job[field])
                job_text = " ".join(job_text_parts).lower()
                
                if not any(kw.lower() in job_text for kw in keywords):
                    continue
            
            # Filter out avoided companies
            if avoid_companies:
                company = job.get("company", "").lower()
                if any(avoid.lower() in company for avoid in avoid_companies):
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def _save_results(self, results: List[Dict]):
        """Save analyzed results to JSON and markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON (full data)
        json_path = f"data/matches_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   📄 JSON saved to {json_path}")
        
        # Save Markdown report (human-readable)
        md_path = f"data/matches_{timestamp}.md"
        self._generate_markdown_report(results, md_path)
        print(f"   📄 Report saved to {md_path}")
    
    def _generate_markdown_report(self, results: List[Dict], filepath: str):
        """Generate a nice markdown report of matches"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# WaterlooWorks Job Matches Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Jobs Analyzed:** {len(results)}\n\n")
            f.write("---\n\n")
            
            # Group by score ranges
            excellent = [r for r in results if r["match"]["fit_score"] >= 70]
            good = [r for r in results if 50 <= r["match"]["fit_score"] < 70]
            moderate = [r for r in results if 30 <= r["match"]["fit_score"] < 50]
            
            f.write(f"## Summary\n\n")
            f.write(f"- 🟢 **Excellent Matches (70+):** {len(excellent)}\n")
            f.write(f"- 🟡 **Good Matches (50-69):** {len(good)}\n")
            f.write(f"- 🟠 **Moderate Matches (30-49):** {len(moderate)}\n\n")
            f.write("---\n\n")
            
            # Write each job
            for i, result in enumerate(results, 1):
                job = result["job"]
                match = result["match"]
                
                # Emoji based on score
                if match["fit_score"] >= 70:
                    emoji = "🟢"
                elif match["fit_score"] >= 50:
                    emoji = "🟡"
                elif match["fit_score"] >= 30:
                    emoji = "🟠"
                else:
                    emoji = "🔴"
                
                f.write(f"## {emoji} #{i} - {job.get('title', 'Unknown')} ({match['fit_score']}/100)\n\n")
                f.write(f"**Company:** {job.get('company', 'N/A')}\n\n")
                f.write(f"**Location:** {job.get('location', 'N/A')}\n\n")
                
                # Match breakdown
                f.write(f"**Match Breakdown:**\n")
                f.write(f"- Coverage: {match['coverage']}%\n")
                f.write(f"- Skill Match: {match['skill_match']}%\n")
                f.write(f"- Seniority Alignment: {match['seniority_alignment']}%\n\n")
                
                # Matched bullets
                if match.get("matched_bullets"):
                    f.write(f"**Your Relevant Experience ({len(match['matched_bullets'])} bullets):**\n\n")
                    for bullet in match["matched_bullets"][:5]:  # Top 5
                        f.write(f"- [{bullet['similarity']:.2f}] {bullet['text']}\n")
                    f.write("\n")
                
                # Job details
                if job.get("summary") or job.get("responsibilities"):
                    f.write(f"**Job Details:**\n\n")
                    if job.get("summary") and job["summary"] != "N/A":
                        f.write(f"{job['summary'][:300]}...\n\n")
                    if job.get("responsibilities") and job["responsibilities"] != "N/A":
                        f.write(f"**Responsibilities:** {job['responsibilities'][:200]}...\n\n")
                
                # Work arrangements
                if job.get("employment_location_arrangement") and job["employment_location_arrangement"] != "N/A":
                    f.write(f"**Location Arrangement:** {job['employment_location_arrangement']}\n\n")
                if job.get("work_term_duration") and job["work_term_duration"] != "N/A":
                    f.write(f"**Work Term:** {job['work_term_duration']}\n\n")
                
                if job.get("url"):
                    f.write(f"**Apply:** {job['url']}\n\n")
                
                f.write("---\n\n")
    
    def _show_summary(self, results: List[Dict]):
        """Show summary in terminal"""
        print("=" * 70)
        print("📊 TOP MATCHES")
        print("=" * 70)
        print()
        
        if not results:
            print("No matches found after filtering.")
            return
        
        # Show top 10
        for i, result in enumerate(results[:10], 1):
            job = result["job"]
            match = result["match"]
            
            # Emoji based on score
            if match["fit_score"] >= 70:
                emoji = "🟢"
            elif match["fit_score"] >= 50:
                emoji = "🟡"
            elif match["fit_score"] >= 30:
                emoji = "🟠"
            else:
                emoji = "🔴"
            
            print(f"{emoji} #{i} - Fit Score: {match['fit_score']}/100")
            print(f"   📋 {job.get('title', 'Unknown')} at {job.get('company', 'N/A')}")
            print(f"   📍 {job.get('location', 'N/A')}")
            print(f"   📈 Coverage: {match['coverage']}% | Skills: {match['skill_match']}% | Seniority: {match['seniority_alignment']}%")
            print()
        
        if len(results) > 10:
            print(f"... and {len(results) - 10} more jobs")
            print()
        
        print("=" * 70)
        print(f"✅ Analysis complete! Check data/ folder for full reports.")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze WaterlooWorks jobs")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (basic scraping, faster)"
    )
    parser.add_argument(
        "--cached",
        action="store_true",
        help="Use cached jobs instead of scraping"
    )
    parser.add_argument(
        "--force-rematch",
        action="store_true",
        help="Ignore cached matches and recalculate all job scores"
    )
    
    args = parser.parse_args()
    
    analyzer = JobAnalyzer()
    
    if args.cached:
        # Load cached jobs
        print("📂 Using cached jobs...")
        with open("data/jobs_scraped.json", 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        print(f"✅ Loaded {len(jobs)} jobs from cache\n")
        
        # Analyze
        print("🔍 Analyzing jobs...")
        if args.force_rematch:
            print("⚠️  Force rematch enabled - ignoring cache")
        results = analyzer.matcher.batch_analyze(jobs, force_rematch=args.force_rematch)
        
        # Filter and save
        filtered = analyzer._apply_filters(results)
        analyzer._save_results(filtered)
        analyzer._show_summary(filtered)
    else:
        # Run full pipeline
        analyzer.run_full_pipeline(detailed=not args.quick, force_rematch=args.force_rematch)


if __name__ == "__main__":
    main()
