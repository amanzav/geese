#!/usr/bin/env python3
"""
Analyze Jobs for Extra Requirements
Uses Gemini AI to identify jobs requiring extra steps beyond standard application
"""

import json
import os
from datetime import datetime
import google.generativeai as genai

# Load environment variables manually
def load_env():
    """Load .env file manually"""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def analyze_job_requirements(job_data, model):
    """
    Use Gemini to analyze a job's additional_info field for extra requirements
    
    Returns:
        dict with 'has_extra', 'category', 'details', 'action_items'
    """
    additional_info = job_data.get("additional_info", "N/A")
    
    if not additional_info or additional_info == "N/A":
        return {
            "has_extra": False,
            "category": "Standard Application",
            "details": "No additional requirements found",
            "action_items": []
        }
    
    prompt = f"""Analyze this job posting's additional information and determine if the applicant needs to take EXTRA steps beyond the standard WaterlooWorks application (resume + cover letter).

Job Title: {job_data.get('title', 'N/A')}
Company: {job_data.get('company', 'N/A')}
Additional Information:
{additional_info}

Categorize the extra requirements into ONE of these categories:
1. EXTERNAL_APPLICATION - Must apply on external website/portal in addition to WaterlooWorks
2. EXTRA_DOCUMENTS - Requires documents beyond resume/cover letter (transcripts, portfolio, references, etc.)
3. DIRECT_CONTACT - Must email/contact employer directly
4. SPECIAL_INSTRUCTIONS - Has specific application instructions or conditions (e.g., citizenship requirements, security clearance, must include portfolio link)
5. STANDARD - No extra steps required

Respond in JSON format:
{{
    "has_extra": true/false,
    "category": "EXTERNAL_APPLICATION" | "EXTRA_DOCUMENTS" | "DIRECT_CONTACT" | "SPECIAL_INSTRUCTIONS" | "STANDARD",
    "details": "Brief explanation of what's required",
    "action_items": ["Specific step 1", "Specific step 2", ...],
    "external_url": "URL if external application required, else null",
    "required_documents": ["Document 1", "Document 2", ...] (if applicable, else empty list)
}}

Be specific and actionable in the action_items. Extract URLs if mentioned."""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        return result
    except Exception as e:
        print(f"      ⚠️  Error analyzing with Gemini: {e}")
        return {
            "has_extra": False,
            "category": "ANALYSIS_FAILED",
            "details": str(e),
            "action_items": []
        }

def generate_report(jobs_data, api_key):
    """Generate a comprehensive report of jobs requiring extra actions"""
    
    print("\n" + "=" * 70)
    print("🔍 ANALYZING JOBS FOR EXTRA REQUIREMENTS")
    print("=" * 70)
    print()
    
    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # Storage for categorized jobs
    jobs_by_category = {
        "EXTERNAL_APPLICATION": [],
        "EXTRA_DOCUMENTS": [],
        "DIRECT_CONTACT": [],
        "SPECIAL_INSTRUCTIONS": [],
        "STANDARD": [],
        "ANALYSIS_FAILED": []
    }
    
    total_jobs = len(jobs_data)
    print(f"📊 Total jobs to analyze: {total_jobs}\n")
    
    # Analyze each job
    for idx, job in enumerate(jobs_data, 1):
        job_id = job.get("id", "N/A")
        company = job.get("company", "N/A")
        title = job.get("title", "N/A")
        
        print(f"[{idx}/{total_jobs}] {company} - {title}")
        
        result = analyze_job_requirements(job, model)
        
        # Add job info to result
        result["job_id"] = job_id
        result["company"] = company
        result["title"] = title
        result["location"] = job.get("location", "N/A")
        result["deadline"] = job.get("deadline", "N/A")
        
        # Categorize
        category = result.get("category", "STANDARD")
        
        # Handle any unexpected categories
        if category not in jobs_by_category:
            category = "STANDARD"
        
        jobs_by_category[category].append(result)
        
        # Show result
        if result.get("has_extra"):
            print(f"      ⚠️  {category}: {result.get('details', 'N/A')}")
        else:
            print(f"      ✓ Standard application")
        
        print()
    
    # Generate markdown report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"data/extra_requirements_report_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 📋 Jobs Requiring Extra Actions Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## 📊 Summary\n\n")
        external_count = len(jobs_by_category["EXTERNAL_APPLICATION"])
        extra_docs_count = len(jobs_by_category["EXTRA_DOCUMENTS"])
        direct_contact_count = len(jobs_by_category["DIRECT_CONTACT"])
        special_count = len(jobs_by_category["SPECIAL_INSTRUCTIONS"])
        standard_count = len(jobs_by_category["STANDARD"])
        
        f.write(f"- **Total Jobs Analyzed:** {total_jobs}\n")
        f.write(f"- 🔗 **External Application Required:** {external_count}\n")
        f.write(f"- 📎 **Extra Documents Required:** {extra_docs_count}\n")
        f.write(f"- ✉️ **Direct Contact Required:** {direct_contact_count}\n")
        f.write(f"- ⚠️ **Special Instructions:** {special_count}\n")
        f.write(f"- ✅ **Standard Application:** {standard_count}\n\n")
        f.write("---\n\n")
        
        # External Applications
        if jobs_by_category["EXTERNAL_APPLICATION"]:
            f.write("## 🔗 External Application Required\n\n")
            f.write("*These jobs require applying through external portals or company websites in addition to WaterlooWorks.*\n\n")
            
            for job in jobs_by_category["EXTERNAL_APPLICATION"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Job ID:** {job['job_id']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Apply Here](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                f.write(f"**Details:** {job.get('details', 'N/A')}  \n\n")
                
                if job.get('external_url'):
                    f.write(f"**🔗 External Application Link:** {job['external_url']}  \n\n")
                
                if job.get('action_items'):
                    f.write("**Action Items:**\n")
                    for item in job['action_items']:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        # Extra Documents
        if jobs_by_category["EXTRA_DOCUMENTS"]:
            f.write("## 📎 Extra Documents Required\n\n")
            f.write("*These jobs require additional documents beyond resume and cover letter.*\n\n")
            
            for job in jobs_by_category["EXTRA_DOCUMENTS"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Job ID:** {job['job_id']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Apply Here](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                f.write(f"**Details:** {job.get('details', 'N/A')}  \n\n")
                
                if job.get('required_documents'):
                    f.write("**Required Documents:**\n")
                    for doc in job['required_documents']:
                        f.write(f"- {doc}\n")
                    f.write("\n")
                
                if job.get('action_items'):
                    f.write("**Action Items:**\n")
                    for item in job['action_items']:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        # Direct Contact
        if jobs_by_category["DIRECT_CONTACT"]:
            f.write("## ✉️ Direct Contact Required\n\n")
            f.write("*These jobs require contacting the employer directly via email or phone.*\n\n")
            
            for job in jobs_by_category["DIRECT_CONTACT"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Job ID:** {job['job_id']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Apply Here](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                f.write(f"**Details:** {job.get('details', 'N/A')}  \n\n")
                
                if job.get('action_items'):
                    f.write("**Action Items:**\n")
                    for item in job['action_items']:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        # Special Instructions
        if jobs_by_category["SPECIAL_INSTRUCTIONS"]:
            f.write("## ⚠️ Special Instructions\n\n")
            f.write("*These jobs have specific requirements or conditions for application.*\n\n")
            
            for job in jobs_by_category["SPECIAL_INSTRUCTIONS"]:
                f.write(f"### {job['title']}\n")
                f.write(f"**Company:** {job['company']}  \n")
                f.write(f"**Location:** {job['location']}  \n")
                f.write(f"**Job ID:** {job['job_id']}  \n")
                f.write(f"**Deadline:** {job['deadline']}  \n")
                f.write(f"**WaterlooWorks:** [Apply Here](https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job['job_id']})  \n\n")
                
                f.write(f"**Details:** {job.get('details', 'N/A')}  \n\n")
                
                if job.get('action_items'):
                    f.write("**Action Items:**\n")
                    for item in job['action_items']:
                        f.write(f"- {item}\n")
                    f.write("\n")
                
                f.write("---\n\n")
    
    # Print summary
    print("=" * 70)
    print("📊 ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Total Jobs: {total_jobs}")
    print(f"🔗 External Application: {external_count}")
    print(f"📎 Extra Documents: {extra_docs_count}")
    print(f"✉️ Direct Contact: {direct_contact_count}")
    print(f"⚠️ Special Instructions: {special_count}")
    print(f"✅ Standard Application: {standard_count}")
    print()
    print(f"📄 Report saved to: {report_path}")
    print("=" * 70)
    
    return report_path

def main():
    """Main entry point"""
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file")
        print("   Please set GEMINI_API_KEY in your .env file")
        return
    
    # Load jobs data
    jobs_file = "data/jobs_scraped.json"
    if not os.path.exists(jobs_file):
        print(f"❌ Error: {jobs_file} not found")
        print("   Run scraping first with: python main.py --mode batch")
        return
    
    with open(jobs_file, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)
    
    # Generate report
    report_path = generate_report(jobs_data, api_key)
    
    print()
    print("✅ Done! Open the report to see all jobs requiring extra actions.")

if __name__ == "__main__":
    main()
