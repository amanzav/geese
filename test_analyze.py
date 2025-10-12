"""
Quick test script to analyze jobs using cached data
This lets you test the matcher without scraping WaterlooWorks
"""

import json
from modules.matcher import ResumeMatcher


def test_with_sample_jobs():
    """Test with sample WaterlooWorks-style jobs"""
    
    # Sample jobs that mimic WaterlooWorks format
    sample_jobs = [
        {
            "title": "Software Developer - Backend",
            "company": "Shopify",
            "location": "Toronto, ON",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "We're looking for a backend developer to build scalable APIs and microservices. You'll work with Ruby on Rails, PostgreSQL, Redis, and Docker.",
            "required_skills": [
                "Backend API development",
                "Ruby on Rails or similar framework",
                "PostgreSQL or MySQL",
                "Docker and Kubernetes",
                "RESTful API design",
                "Microservices architecture"
            ],
            "additional_requirements": [
                "2+ years of experience",
                "Strong problem-solving skills",
                "Excellent communication"
            ]
        },
        {
            "title": "Full Stack Engineer - Co-op",
            "company": "Amazon",
            "location": "Toronto, ON",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Join our team building AWS management tools. You'll use React, TypeScript, Node.js, and AWS services to create internal dashboards.",
            "required_skills": [
                "React and TypeScript",
                "Node.js backend development",
                "AWS services (Lambda, DynamoDB, S3)",
                "Full stack development",
                "REST APIs"
            ],
            "additional_requirements": [
                "Currently enrolled in Computer Science or related",
                "Strong coding skills"
            ]
        },
        {
            "title": "Embedded Software Engineer",
            "company": "Tesla",
            "location": "Palo Alto, CA",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Develop real-time embedded systems for vehicle control units. Experience with C++, RTOS, and automotive protocols required.",
            "required_skills": [
                "C++ embedded development",
                "Real-time operating systems (RTOS)",
                "CAN bus and automotive protocols",
                "Hardware/software integration",
                "Low-level debugging"
            ],
            "additional_requirements": [
                "Bachelor's in Mechatronics or Computer Engineering",
                "Experience with automotive systems preferred"
            ]
        },
        {
            "title": "Mobile Developer - iOS/Android",
            "company": "Meta",
            "location": "Menlo Park, CA",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Build mobile features for Facebook and Instagram apps. Work with Swift, Kotlin, and React Native.",
            "required_skills": [
                "React Native development",
                "iOS (Swift) or Android (Kotlin)",
                "Mobile UI/UX best practices",
                "RESTful APIs and GraphQL",
                "Performance optimization"
            ],
            "additional_requirements": [
                "2+ years mobile development",
                "Published apps on App Store or Play Store"
            ]
        },
        {
            "title": "DevOps Engineer Intern",
            "company": "Google",
            "location": "Waterloo, ON",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Automate infrastructure and deployment pipelines. Experience with Kubernetes, Terraform, and CI/CD required.",
            "required_skills": [
                "Docker and Kubernetes",
                "CI/CD pipelines (Jenkins, GitHub Actions)",
                "Infrastructure as Code (Terraform, Ansible)",
                "Cloud platforms (GCP, AWS, Azure)",
                "Python or Go scripting"
            ],
            "additional_requirements": [
                "Strong Linux/Unix skills",
                "Problem-solving mindset"
            ]
        },
        {
            "title": "Machine Learning Engineer",
            "company": "OpenAI",
            "location": "San Francisco, CA",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Train and deploy large language models. Work with PyTorch, distributed training, and model optimization.",
            "required_skills": [
                "Python and PyTorch/TensorFlow",
                "Machine learning fundamentals",
                "LLM training and fine-tuning",
                "Distributed computing",
                "GPU optimization"
            ],
            "additional_requirements": [
                "PhD or Master's in ML/AI preferred",
                "Published research papers"
            ]
        },
        {
            "title": "Software Engineer - Infra",
            "company": "Uber",
            "location": "Toronto, ON",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Build infrastructure tools and services. Work with Go, Python, Kubernetes, and distributed systems.",
            "required_skills": [
                "Python or Go development",
                "Distributed systems",
                "Kubernetes and Docker",
                "Database systems (PostgreSQL, Redis)",
                "System design and architecture"
            ],
            "additional_requirements": [
                "Strong CS fundamentals",
                "3+ years of experience"
            ]
        },
        {
            "title": "Frontend Engineer - React",
            "company": "Airbnb",
            "location": "Remote",
            "url": "https://waterlooworks.uwaterloo.ca/...",
            "description": "Build beautiful user interfaces for Airbnb's platform. Expert in React, TypeScript, and modern CSS.",
            "required_skills": [
                "React and TypeScript",
                "Modern CSS (Tailwind, Styled Components)",
                "Component libraries and design systems",
                "Performance optimization",
                "Accessibility (a11y)"
            ],
            "additional_requirements": [
                "Portfolio of web applications",
                "Eye for design"
            ]
        }
    ]
    
    print("=" * 70)
    print("🧪 Testing Job Matcher with Sample Jobs")
    print("=" * 70)
    print()
    
    # Initialize matcher
    print("📦 Loading matcher...")
    matcher = ResumeMatcher()
    
    # Analyze jobs
    print(f"🔍 Analyzing {len(sample_jobs)} jobs...\n")
    results = matcher.batch_analyze(sample_jobs)
    
    # Show results
    print()
    print("=" * 70)
    print("📊 RESULTS (Sorted by Fit Score)")
    print("=" * 70)
    print()
    
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
        
        print(f"{emoji} #{i} - Fit Score: {match['fit_score']}/100")
        print(f"   📋 {job['title']}")
        print(f"   🏢 {job['company']} - {job['location']}")
        print(f"   📈 Coverage: {match['coverage']}% | Skills: {match['skill_match']}% | Seniority: {match['seniority_alignment']}%")
        
        # Show top 2 matched bullets
        if match['matched_bullets']:
            print(f"   ✨ Top matches:")
            for bullet in match['matched_bullets'][:2]:
                text = bullet['text'][:65] + "..." if len(bullet['text']) > 65 else bullet['text']
                print(f"      • [{bullet['similarity']:.2f}] {text}")
        
        print()
    
    print("=" * 70)
    print("✅ Test complete!")
    print("=" * 70)
    
    # Save results
    with open("data/test_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Results saved to data/test_results.json")


if __name__ == "__main__":
    test_with_sample_jobs()
