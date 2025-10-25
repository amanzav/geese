#!/usr/bin/env python3
"""
Quick Analysis - Extract jobs requiring extra steps from jobs_scraped.json
Uses simple text analysis instead of AI for faster results
"""

import json
import re
from datetime import datetime

def analyze_job(job):
    """Simple text-based analysis of job requirements"""
    additional_info = job.get("additional_info", "N/A")
    
    if not additional_info or additional_info == "N/A":
        return None
    
    result = {
        "job_id": job.get("id", "N/A"),
        "company": job.get("company", "N/A"),
        "title": job.get("title", "N/A"),
        "location": job.get("location", "N/A"),
        "deadline": job.get("deadline", "N/A"),
        "category": "",
        "details": additional_info,
        "action_items": []
    }
    
    lower_info = additional_info.lower()
    
    # External application patterns
    external_patterns = [
        r'apply.*(?:through|via|at|to).*(?:https?://\S+)',
        r'interested applicants must apply.*(?:https?://\S+)',
        r'application.*(?:https?://\S+)',
        r'apply directly.*(?:https?://\S+)'
    ]
    
    for pattern in external_patterns:
        if re.search(pattern, lower_info, re.IGNORECASE):
            result["category"] = "EXTERNAL_APPLICATION"
            urls = re.findall(r'https?://\S+', additional_info)
            if urls:
                result["external_url"] = urls[0]
                result["action_items"].append(f"Apply at: {urls[0]}")
            break
    
    # Extra documents patterns
    doc_keywords = [
        'transcript', 'portfolio', 'references', 'reference letter',
        'cover letter is required', 'must include', 'writing sample',
        'work sample', 'proof of', 'police check', 'security clearance'
    ]
    
    if not result["category"]:
        for keyword in doc_keywords:
            if keyword in lower_info:
                result["category"] = "EXTRA_DOCUMENTS"
                result["action_items"].append(f"Prepare: {keyword}")
                break
    
    # Direct contact patterns
    contact_patterns = [
        'contact.*directly',
        'email.*to apply',
        'send.*resume.*to'
    ]
    
    if not result["category"]:
        for pattern in contact_patterns:
            if re.search(pattern, lower_info, re.IGNORECASE):
                result["category"] = "DIRECT_CONTACT"
                emails = re.findall(r'\S+@\S+', additional_info)
                if emails:
                    result["action_items"].append(f"Email: {emails[0]}")
                break
    
    # Special instructions (citizenship, clearance, specific requirements)
    special_keywords = [
        'citizen', 'clearance', 'eligibility', 'form letter',
        'specific', 'requirement', 'must be'
    ]
    
    if not result["category"]:
        for keyword in special_keywords:
            if keyword in lower_info:
                result["category"] = "SPECIAL_INSTRUCTIONS"
                result["action_items"].append(f"Note: Check requirements for {keyword}")
                break
    
    # If still no category but has additional_info, mark as special
    if not result["category"] and len(additional_info) > 50:
        result["category"] = "SPECIAL_INSTRUCTIONS"
        result["action_items"].append("Review additional information carefully")
    
    return result if result["category"] else None

def main():
    """Main entry point"""
    
    print("\n" + "=" * 70)
    print("📋 QUICK ANALYSIS: Jobs Requiring Extra Actions")
    print("=" * 70)
    print()
    
    # Load jobs
    jobs_file = "data/jobs_scraped.json"
    with open(jobs_file, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)
    
    print(f"📊 Analyzing {len(jobs_data)} jobs...\n")
    
    # Categorize jobs
    extra_requirement_jobs = []
    
    for idx, job in enumerate(jobs_data, 1):
        result = analyze_job(job)
        if result:
            extra_requirement_jobs.append(result)
            print(f"[{idx}/{len(jobs_data)}] {result['company']} - {result['title']}")
            print(f"      ⚠️  {result['category']}")
    
    print(f"\n✅ Found {len(extra_requirement_jobs)} jobs with extra requirements\n")
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"data/extra_requirements_quick_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 📋 Jobs Requiring Extra Actions - Quick Analysis\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Jobs Analyzed:** {len(jobs_data)}\n")
        f.write(f"**Jobs with Extra Requirements:** {len(extra_requirement_jobs)}\n\n")
        f.write("---\n\n")
        
        # Group by category
        by_category = {}
        for job in extra_requirement_jobs:
            cat = job["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(job)
        
        # External Applications
        if "EXTERNAL_APPLICATION" in by_category:
            f.write("## 🔗 External Application Required\n\n")
            for job in by_category["EXTERNAL_APPLICATION"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Job #{job['job_id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                if job.get("external_url"):
                    f.write(f"**🔗 External Link:** {job['external_url']}  \n\n")
                
                if job["action_items"]:
                    f.write("**Action Items:**\n")
                    for item in job["action_items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write(f"**Additional Info:**\n{job['details']}\n\n")
                f.write("---\n\n")
        
        # Extra Documents
        if "EXTRA_DOCUMENTS" in by_category:
            f.write("## 📎 Extra Documents Required\n\n")
            for job in by_category["EXTRA_DOCUMENTS"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Job #{job['job_id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                if job["action_items"]:
                    f.write("**Action Items:**\n")
                    for item in job["action_items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write(f"**Additional Info:**\n{job['details']}\n\n")
                f.write("---\n\n")
        
        # Direct Contact
        if "DIRECT_CONTACT" in by_category:
            f.write("## ✉️ Direct Contact Required\n\n")
            for job in by_category["DIRECT_CONTACT"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Job #{job['job_id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                if job["action_items"]:
                    f.write("**Action Items:**\n")
                    for item in job["action_items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write(f"**Additional Info:**\n{job['details']}\n\n")
                f.write("---\n\n")
        
        # Special Instructions
        if "SPECIAL_INSTRUCTIONS" in by_category:
            f.write("## ⚠️ Special Instructions\n\n")
            for job in by_category["SPECIAL_INSTRUCTIONS"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Job #{job['job_id']}](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                if job["action_items"]:
                    f.write("**Action Items:**\n")
                    for item in job["action_items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write(f"**Additional Info:**\n{job['details']}\n\n")
                f.write("---\n\n")
    
    print("=" * 70)
    print("📄 REPORT GENERATED")
    print("=" * 70)
    print(f"Report saved to: {report_path}")
    print()
    
    # Summary
    for cat, jobs in by_category.items():
        emoji = {"EXTERNAL_APPLICATION": "🔗", "EXTRA_DOCUMENTS": "📎", "DIRECT_CONTACT": "✉️", "SPECIAL_INSTRUCTIONS": "⚠️"}.get(cat, "📋")
        print(f"{emoji} {cat.replace('_', ' ').title()}: {len(jobs)}")
    
    print()
    print("✅ Done! Open the report to see all details.")
    print("=" * 70)

if __name__ == "__main__":
    main()
