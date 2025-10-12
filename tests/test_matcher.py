"""
Test Resume Matcher
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.matcher import ResumeMatcher


def test_matcher():
    """Test resume matcher with sample jobs"""
    
    print("=" * 70)
    print("🧪 Testing Resume Matcher")
    print("=" * 70)
    print()
    
    # Initialize matcher
    print("📦 Initializing matcher...")
    matcher = ResumeMatcher()
    print()
    
    # Sample jobs (simulating scraper output)
    sample_jobs = [
        {
            "title": "Full Stack Developer",
            "company": "Tech Corp",
            "location": "Toronto",
            "description": "Looking for a full stack developer to build modern web applications.",
            "required_skills": [
                "React Native mobile development",
                "Node.js backend APIs",
                "AWS cloud infrastructure",
                "PostgreSQL databases",
                "Docker and container orchestration"
            ],
            "additional_requirements": [
                "3+ years of experience",
                "Strong communication skills"
            ]
        },
        {
            "title": "Backend Engineer",
            "company": "DataTech Inc",
            "location": "Remote",
            "description": "Build scalable data pipelines and APIs.",
            "required_skills": [
                "Python backend development",
                "AWS Lambda and serverless",
                "PostgreSQL and database optimization",
                "REST API design",
                "Data pipeline experience"
            ],
            "additional_requirements": [
                "Experience with Airflow or similar",
                "Strong SQL skills"
            ]
        },
        {
            "title": "Senior Frontend Engineer",
            "company": "UI Solutions",
            "location": "Waterloo",
            "description": "Lead frontend development for our SaaS platform.",
            "required_skills": [
                "React.js and modern JavaScript",
                "TypeScript",
                "Component libraries and design systems",
                "Performance optimization",
                "Mentoring junior developers"
            ],
            "additional_requirements": [
                "5+ years frontend experience",
                "Leadership experience"
            ]
        },
        {
            "title": "Machine Learning Engineer",
            "company": "AI Systems",
            "location": "Toronto",
            "description": "Build and deploy ML models at scale.",
            "required_skills": [
                "Python machine learning",
                "TensorFlow or PyTorch",
                "Model deployment and MLOps",
                "Cloud infrastructure (AWS/GCP)",
                "SQL and data processing"
            ],
            "additional_requirements": [
                "PhD or Masters in CS/ML preferred",
                "Research publications"
            ]
        }
    ]
    
    # Analyze all jobs
    print("🔍 Analyzing jobs...\n")
    results = matcher.batch_analyze(sample_jobs)
    
    # Print results
    print()
    print("=" * 70)
    print("📊 RESULTS (sorted by fit score)")
    print("=" * 70)
    print()
    
    for i, result in enumerate(results, 1):
        job = result["job"]
        match = result["match"]
        
        # Color code based on fit score
        if match["fit_score"] >= 70:
            emoji = "🟢"
        elif match["fit_score"] >= 50:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        print(f"{emoji} #{i} - Fit Score: {match['fit_score']}/100")
        print(f"   📋 {job['title']} at {job['company']}")
        print(f"   📍 {job['location']}")
        print(f"   📈 Coverage: {match['coverage']}% | Skills: {match['skill_match']}% | Seniority: {match['seniority_alignment']}%")
        print(f"   ✨ {len(match['matched_bullets'])} bullets matched")
        
        # Show top 3 matched bullets
        if match['matched_bullets']:
            print(f"   Top matches:")
            for j, bullet in enumerate(match['matched_bullets'][:3], 1):
                text = bullet['text'][:70] + "..." if len(bullet['text']) > 70 else bullet['text']
                print(f"      {j}. [{bullet['similarity']:.2f}] {text}")
        
        print()
    
    print("=" * 70)
    print("✅ Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_matcher()
