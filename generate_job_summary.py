"""
Generate a markdown summary of jobs from folder-scraped JSON
"""

import json
import sys
from pathlib import Path


def format_compensation(comp_data):
    """Format compensation data into readable string"""
    if isinstance(comp_data, dict):
        if comp_data.get("value"):
            value = comp_data["value"]
            currency = comp_data.get("currency", "CAD")
            time_period = comp_data.get("time_period", "unknown")
            
            if time_period == "hourly":
                return f"${value:.2f}/{time_period} ({currency})"
            elif time_period == "monthly":
                return f"${value:,.0f}/{time_period} ({currency})"
            elif time_period == "yearly":
                return f"${value:,.0f}/{time_period} ({currency})"
        
        # Fallback to original text
        if comp_data.get("original_text"):
            return comp_data["original_text"]
    
    return "Not specified"


def generate_job_markdown(jobs_file, output_file):
    """Generate markdown summary from jobs JSON"""
    
    # Load jobs
    with open(jobs_file, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    # Start markdown content
    md_content = []
    md_content.append("# Job Opportunities Summary")
    md_content.append(f"\n**Total Jobs:** {len(jobs)}")
    md_content.append(f"\n**Generated:** {Path(jobs_file).stem.replace('jobs_', '').replace('_', ' ').title()} Folder")
    md_content.append("\n---\n")
    
    # Count jobs by category
    external_apps = sum(1 for j in jobs if j.get('requirements', {}).get('external_application', {}).get('required'))
    extra_docs = sum(1 for j in jobs if j.get('requirements', {}).get('extra_documents', {}).get('required'))
    bonus_items = sum(1 for j in jobs if j.get('requirements', {}).get('bonus_items', {}).get('available'))
    
    md_content.append("## Quick Stats\n")
    md_content.append(f"- 🔗 **External Applications Required:** {external_apps}")
    md_content.append(f"- 📎 **Extra Documents Required:** {extra_docs}")
    md_content.append(f"- ⭐ **Bonus Items Available:** {bonus_items}")
    md_content.append(f"- ✅ **Standard Applications:** {len(jobs) - external_apps - extra_docs - bonus_items}")
    md_content.append("\n---\n")
    
    # Group jobs by requirement type
    external_jobs = []
    extra_doc_jobs = []
    bonus_jobs = []
    standard_jobs = []
    
    for job in jobs:
        reqs = job.get('requirements', {})
        if reqs.get('external_application', {}).get('required'):
            external_jobs.append(job)
        elif reqs.get('extra_documents', {}).get('required'):
            extra_doc_jobs.append(job)
        elif reqs.get('bonus_items', {}).get('available'):
            bonus_jobs.append(job)
        else:
            standard_jobs.append(job)
    
    # External Applications Section
    if external_jobs:
        md_content.append("## 🔗 External Applications Required\n")
        md_content.append(f"*{len(external_jobs)} jobs require applying through external websites*\n")
        for job in external_jobs:
            md_content.append(f"\n### {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
            md_content.append(f"**ID:** {job.get('id', 'N/A')}")
            md_content.append(f"**Location:** {job.get('location', 'N/A')}")
            md_content.append(f"**Level:** {job.get('level', 'N/A')}")
            md_content.append(f"**Deadline:** {job.get('deadline', 'N/A')}")
            md_content.append(f"**Applications:** {job.get('applications', 'N/A')} | **Openings:** {job.get('openings', 'N/A')}")
            
            # Compensation
            comp = format_compensation(job.get('compensation', {}))
            md_content.append(f"**Compensation:** {comp}")
            
            # External application details
            ext_app = job.get('requirements', {}).get('external_application', {})
            url = ext_app.get('url')
            if url:
                md_content.append(f"**⚠️ External Application URL:** {url}")
            else:
                md_content.append("**⚠️ External application required (see additional info)**")
            
            md_content.append("")
    
    # Extra Documents Section
    if extra_doc_jobs:
        md_content.append("\n---\n")
        md_content.append("## 📎 Extra Documents Required\n")
        md_content.append(f"*{len(extra_doc_jobs)} jobs require documents beyond resume/cover letter*\n")
        for job in extra_doc_jobs:
            md_content.append(f"\n### {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
            md_content.append(f"**ID:** {job.get('id', 'N/A')}")
            md_content.append(f"**Location:** {job.get('location', 'N/A')}")
            md_content.append(f"**Level:** {job.get('level', 'N/A')}")
            md_content.append(f"**Deadline:** {job.get('deadline', 'N/A')}")
            md_content.append(f"**Applications:** {job.get('applications', 'N/A')} | **Openings:** {job.get('openings', 'N/A')}")
            
            # Compensation
            comp = format_compensation(job.get('compensation', {}))
            md_content.append(f"**Compensation:** {comp}")
            
            # Extra documents
            extra_docs = job.get('requirements', {}).get('extra_documents', {})
            docs = extra_docs.get('documents', [])
            if docs:
                md_content.append(f"**📎 Required Documents:** {', '.join(docs)}")
            
            md_content.append("")
    
    # Bonus Items Section
    if bonus_jobs:
        md_content.append("\n---\n")
        md_content.append("## ⭐ Bonus Items Available\n")
        md_content.append(f"*{len(bonus_jobs)} jobs have optional items to stand out*\n")
        for job in bonus_jobs:
            md_content.append(f"\n### {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
            md_content.append(f"**ID:** {job.get('id', 'N/A')}")
            md_content.append(f"**Location:** {job.get('location', 'N/A')}")
            md_content.append(f"**Level:** {job.get('level', 'N/A')}")
            md_content.append(f"**Deadline:** {job.get('deadline', 'N/A')}")
            md_content.append(f"**Applications:** {job.get('applications', 'N/A')} | **Openings:** {job.get('openings', 'N/A')}")
            
            # Compensation
            comp = format_compensation(job.get('compensation', {}))
            md_content.append(f"**Compensation:** {comp}")
            
            # Bonus items
            bonus = job.get('requirements', {}).get('bonus_items', {})
            items = bonus.get('items', [])
            if items:
                md_content.append(f"**⭐ Bonus Items:** {', '.join(items)}")
            else:
                md_content.append("**⭐ Bonus items available (see additional info)**")
            
            md_content.append("")
    
    # Standard Jobs Section
    if standard_jobs:
        md_content.append("\n---\n")
        md_content.append("## ✅ Standard Applications\n")
        md_content.append(f"*{len(standard_jobs)} jobs with standard application process*\n")
        for job in standard_jobs:
            md_content.append(f"\n### {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
            md_content.append(f"**ID:** {job.get('id', 'N/A')}")
            md_content.append(f"**Location:** {job.get('location', 'N/A')}")
            md_content.append(f"**Level:** {job.get('level', 'N/A')}")
            md_content.append(f"**Deadline:** {job.get('deadline', 'N/A')}")
            md_content.append(f"**Applications:** {job.get('applications', 'N/A')} | **Openings:** {job.get('openings', 'N/A')}")
            
            # Compensation
            comp = format_compensation(job.get('compensation', {}))
            md_content.append(f"**Compensation:** {comp}")
            
            md_content.append("")
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"✅ Generated markdown summary: {output_file}")
    print(f"   Total jobs: {len(jobs)}")
    print(f"   - External applications: {len(external_jobs)}")
    print(f"   - Extra documents: {len(extra_doc_jobs)}")
    print(f"   - Bonus items: {len(bonus_jobs)}")
    print(f"   - Standard: {len(standard_jobs)}")


if __name__ == "__main__":
    # Default paths
    jobs_file = "data/jobs_good_shit.json"
    output_file = "data/jobs_good_shit_summary.md"
    
    # Allow command-line arguments
    if len(sys.argv) > 1:
        jobs_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    # Check if jobs file exists
    if not Path(jobs_file).exists():
        print(f"❌ Error: Jobs file not found: {jobs_file}")
        sys.exit(1)
    
    # Generate summary
    generate_job_markdown(jobs_file, output_file)
