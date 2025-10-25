#!/usr/bin/env python3
"""
Concise Analysis - Uses text patterns for initial filtering, then Gemini for critical jobs
Generates a short, actionable report
"""

import json
import re
import os
from datetime import datetime
import google.generativeai as genai

def load_env():
    """Load environment variables from .env file"""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def quick_categorize(job):
    """Quick text-based categorization"""
    additional_info = job.get("additional_info", "N/A")
    
    if not additional_info or additional_info == "N/A" or len(additional_info) < 30:
        return None
    
    lower_info = additional_info.lower()
    
    # External application
    if re.search(r'apply.*(?:through|via|at|to).*https?://', lower_info, re.IGNORECASE):
        urls = re.findall(r'https?://\S+', additional_info)
        return {"category": "EXTERNAL_APPLICATION", "url": urls[0] if urls else None, "info": additional_info}
    
    # Extra documents (high priority ones)
    high_priority_docs = ['transcript', 'portfolio', 'reference letter', 'writing sample', 'work sample']
    for doc in high_priority_docs:
        if doc in lower_info:
            return {"category": "EXTRA_DOCUMENTS", "doc_type": doc, "info": additional_info}
    
    # Bonus/stand-out items (optional but valuable)
    bonus_keywords = ['optional', 'bonus', 'stand out', 'set you apart', 'preferred', 'nice to have', 'showcase']
    if any(keyword in lower_info for keyword in bonus_keywords):
        return {"category": "BONUS_ITEMS", "info": additional_info}
    
    # Special requirements (citizenship, clearance, etc.)
    if any(keyword in lower_info for keyword in ['citizen', 'clearance', 'eligibility', 'proof of']):
        return {"category": "SPECIAL", "info": additional_info}
    
    return None

def analyze_with_gemini(job, model):
    """Use Gemini to analyze critical jobs for better details"""
    additional_info = job.get("additional_info", "N/A")
    
    prompt = f"""Analyze this job posting's additional requirements and provide a BRIEF summary:

Job: {job.get('title')} at {job.get('company')}
Additional Info: {additional_info}

Provide ONLY:
1. Type: EXTERNAL_APP / EXTRA_DOCS / BONUS_ITEMS / SPECIAL_REQ
2. Key action (1 sentence max)
3. If external app: the URL
4. If extra docs: list specific documents needed
5. If bonus items: what optional things make you stand out (e.g., portfolio, project demo, specific skills)

Format as JSON:
{{"type": "...", "action": "...", "url": "...", "docs": [], "bonus_items": []}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text
        
        return json.loads(json_str)
    except Exception as e:
        return {"type": "ANALYSIS_FAILED", "action": "Review manually", "error": str(e)}

def main():
    """Main entry point"""
    
    print("\n" + "=" * 70)
    print("📋 CONCISE ANALYSIS: Critical Jobs Requiring Extra Actions")
    print("=" * 70)
    print()
    
    # Load environment
    load_env()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file")
        return
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # Load jobs
    jobs_file = "data/jobs_scraped.json"
    with open(jobs_file, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)
    
    print(f"📊 Analyzing {len(jobs_data)} jobs...\n")
    
    # Quick filter
    print("Step 1: Quick text-based filtering...")
    critical_jobs = []
    
    for job in jobs_data:
        result = quick_categorize(job)
        if result:
            critical_jobs.append({
                "job": job,
                "quick_analysis": result
            })
    
    print(f"✅ Found {len(critical_jobs)} jobs with potential extra requirements\n")
    
    # Use Gemini for high-priority jobs only
    print("Step 2: Deep analysis with Gemini for critical jobs...")
    
    external_apps = []
    extra_docs = []
    bonus_items = []
    special_reqs = []
    
    for idx, item in enumerate(critical_jobs, 1):
        job = item["job"]
        quick = item["quick_analysis"]
        
        # Use Gemini for external apps, extra docs, AND bonus items
        if quick["category"] in ["EXTERNAL_APPLICATION", "EXTRA_DOCUMENTS", "BONUS_ITEMS"]:
            print(f"  [{idx}/{len(critical_jobs)}] Analyzing {job.get('company')}...")
            gemini_result = analyze_with_gemini(job, model)
            
            entry = {
                "id": job.get("id"),
                "company": job.get("company"),
                "title": job.get("title"),
                "deadline": job.get("deadline"),
                "analysis": gemini_result
            }
            
            if quick["category"] == "EXTERNAL_APPLICATION":
                external_apps.append(entry)
            elif quick["category"] == "EXTRA_DOCUMENTS":
                extra_docs.append(entry)
            else:  # BONUS_ITEMS
                bonus_items.append(entry)
        else:
            # Special requirements - no Gemini needed
            special_reqs.append({
                "id": job.get("id"),
                "company": job.get("company"),
                "title": job.get("title"),
                "deadline": job.get("deadline"),
                "info": quick["info"]
            })
    
    print(f"\n✅ Deep analysis complete!\n")
    
    # Generate concise report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"data/extra_requirements_concise_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 🎯 Jobs Requiring Extra Actions - Concise Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- 🔗 External Applications: **{len(external_apps)}**\n")
        f.write(f"- 📎 Extra Documents: **{len(extra_docs)}**\n")
        f.write(f"- ⭐ Bonus/Stand-Out Items: **{len(bonus_items)}**\n")
        f.write(f"- ⚠️ Special Requirements: **{len(special_reqs)}**\n")
        f.write(f"- ✅ Standard Applications: **{len(jobs_data) - len(critical_jobs)}**\n\n")
        f.write("---\n\n")
        
        # External Applications - Most Important
        if external_apps:
            f.write("## 🔗 PRIORITY: External Applications\n\n")
            f.write("**Action Required:** Apply on BOTH WaterlooWorks AND external portal\n\n")
            
            for job in external_apps:
                f.write(f"### {job['company']} - {job['title']}\n")
                f.write(f"- **Deadline:** {job['deadline']}\n")
                f.write(f"- **WW Link:** [Job #{job['id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['id']})\n")
                
                analysis = job['analysis']
                if analysis.get('url'):
                    f.write(f"- **🔗 Apply Here:** {analysis['url']}\n")
                f.write(f"- **Action:** {analysis.get('action', 'Apply via external link')}\n\n")
            
            f.write("---\n\n")
        
        # Extra Documents
        if extra_docs:
            f.write("## 📎 Extra Documents Required\n\n")
            
            for job in extra_docs:
                f.write(f"### {job['company']} - {job['title']}\n")
                f.write(f"- **Deadline:** {job['deadline']}\n")
                f.write(f"- **WW Link:** [Job #{job['id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['id']})\n")
                
                analysis = job['analysis']
                if analysis.get('docs'):
                    f.write(f"- **📋 Prepare:** {', '.join(analysis['docs'])}\n")
                f.write(f"- **Action:** {analysis.get('action', 'Prepare required documents')}\n\n")
            
            f.write("---\n\n")
        
        # Bonus/Stand-Out Items - NEW SECTION
        if bonus_items:
            f.write("## ⭐ BONUS: Make Your Application Stand Out\n\n")
            f.write("**Note:** These are OPTIONAL but can significantly improve your chances!\n\n")
            
            for job in bonus_items:
                f.write(f"### {job['company']} - {job['title']}\n")
                f.write(f"- **Deadline:** {job['deadline']}\n")
                f.write(f"- **WW Link:** [Job #{job['id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['id']})\n")
                
                analysis = job['analysis']
                if analysis.get('bonus_items'):
                    f.write(f"- **⭐ Stand Out With:** {', '.join(analysis['bonus_items'])}\n")
                f.write(f"- **Action:** {analysis.get('action', 'Add optional materials to stand out')}\n\n")
            
            f.write("---\n\n")
        
        # Special Requirements - Condensed
        if special_reqs:
            f.write("## ⚠️ Special Requirements (Review Before Applying)\n\n")
            f.write("**Note:** These jobs have special conditions. Review carefully.\n\n")
            
            f.write("| Company | Title | Deadline | Note |\n")
            f.write("|---------|-------|----------|------|\n")
            
            for job in special_reqs[:20]:  # Limit to 20 most recent
                info_short = job['info'][:80] + "..." if len(job['info']) > 80 else job['info']
                info_short = info_short.replace('\n', ' ').replace('|', '\\|')
                f.write(f"| {job['company'][:30]} | {job['title'][:40]} | {job['deadline']} | {info_short} |\n")
            
            if len(special_reqs) > 20:
                f.write(f"\n*+ {len(special_reqs) - 20} more jobs with special requirements. Check WaterlooWorks for details.*\n")
            
            f.write("\n---\n\n")
        
        # Quick stats footer
        f.write("## 📊 Application Strategy\n\n")
        f.write(f"1. **High Priority:** {len(external_apps)} external applications - do these first!\n")
        f.write(f"2. **Prepare Docs:** {len(extra_docs)} jobs need extra documents - gather these\n")
        f.write(f"3. **Stand Out:** {len(bonus_items)} jobs have optional bonus items - prepare if you want to impress\n")
        f.write(f"4. **Review Special:** {len(special_reqs)} jobs have special requirements\n")
        f.write(f"5. **Automate Rest:** {len(jobs_data) - len(critical_jobs)} standard jobs - use automation\n\n")
        f.write("**Ready to automate?** Run: `python main.py --mode apply --max-apps 50`\n")
    
    print("=" * 70)
    print("📄 CONCISE REPORT GENERATED")
    print("=" * 70)
    print(f"Report saved to: {report_path}")
    print()
    print(f"🔗 External Applications: {len(external_apps)}")
    print(f"📎 Extra Documents: {len(extra_docs)}")
    print(f"⭐ Bonus/Stand-Out Items: {len(bonus_items)}")
    print(f"⚠️ Special Requirements: {len(special_reqs)}")
    print(f"✅ Standard Jobs: {len(jobs_data) - len(critical_jobs)}")
    print()
    print("✅ Done! Much shorter report - only the essentials.")
    print("=" * 70)

if __name__ == "__main__":
    main()
