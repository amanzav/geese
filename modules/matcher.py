"""
Resume Matcher - Matches job descriptions to resume using embeddings
"""

import json
import os
from typing import Dict, List
from pypdf import PdfReader

from modules.embeddings import EmbeddingsManager


def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


class ResumeMatcher:
    """Analyzes job descriptions against resume to calculate match scores"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize matcher with configuration"""
        self.config = load_config(config_path)
        self.matcher_config = self.config.get("matcher", {})
        
        # Initialize embeddings manager
        model_name = self.matcher_config.get("embedding_model")
        self.embeddings = EmbeddingsManager(model_name=model_name)
        
        # Load resume
        self.resume_bullets = self._load_resume()
        
        # Build or load resume index
        if self.embeddings.index_exists():
            print("📂 Loading cached resume embeddings...")
            self.embeddings.load_index()
        else:
            print("🔨 Building resume embeddings...")
            self.embeddings.build_resume_index(self.resume_bullets)
        
        print(f"✅ Resume loaded with {len(self.resume_bullets)} bullets\n")
    
    def _load_resume(self) -> List[str]:
        """Load resume from cached text file or PDF"""
        cached_path = "data/resume_parsed.txt"
        
        if os.path.exists(cached_path):
            print(f"📄 Loading resume from {cached_path}")
            with open(cached_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        
        # Extract from PDF if no cache
        resume_path = self.config.get("resume_path", "input/resume.pdf")
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
        
        print(f"📄 Extracting text from {resume_path}")
        bullets = self._extract_bullets_from_pdf(resume_path)
        
        # Cache for future use
        os.makedirs("data", exist_ok=True)
        with open(cached_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(bullets))
        
        return bullets
    
    def _extract_bullets_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract bullet points from resume PDF"""
        reader = PdfReader(pdf_path)
        text = "".join(page.extract_text() for page in reader.pages)
        
        bullets = []
        for line in text.split('\n'):
            line = line.strip()
            
            # Remove bullet symbols
            for symbol in ['•', '●', '◦', '▪', '-', '*']:
                if line.startswith(symbol):
                    line = line[1:].strip()
            
            # Keep lines that look like experience bullets
            if 20 <= len(line) <= 300 and not line.endswith(':'):
                bullets.append(line)
        
        if not bullets:
            raise ValueError("No bullet points found in resume")
        
        return bullets
    
    def _parse_job_to_requirements(self, job: Dict) -> List[str]:
        """Convert job data from scraper to requirement bullets"""
        requirements = []
        
        if job.get("title"):
            requirements.append(f"Experience in {job['title']} role")
        
        if job.get("required_skills"):
            requirements.extend(skill.strip() for skill in job["required_skills"] if skill.strip())
        
        if job.get("additional_requirements"):
            requirements.extend(req.strip() for req in job["additional_requirements"] if req.strip())
        
        # Fallback to description if no structured data
        if not requirements and job.get("description"):
            desc = job["description"]
            sentences = [s.strip() for s in desc.split('.') if 20 <= len(s.strip()) <= 200]
            requirements = sentences[:10]
        
        return requirements
    
    def analyze_match(self, job: Dict) -> Dict:
        """Analyze how well resume matches a job"""
        requirements = self._parse_job_to_requirements(job)
        
        if not requirements:
            return {
                "fit_score": 0,
                "matched_bullets": [],
                "coverage": 0,
                "skill_match": 0,
                "seniority_alignment": 50,
                "error": "No requirements found in job"
            }
        
        # Search for matching resume bullets
        top_k = self.matcher_config.get("top_k", 8)
        threshold = self.matcher_config.get("similarity_threshold", 0.50)
        results = self.embeddings.search(requirements, k=top_k)
        
        # Collect unique matched bullets
        matched_bullets_map = {}
        for req_matches in results:
            for match in req_matches:
                bullet_text = self.resume_bullets[match["index"]]
                similarity = match["similarity"]
                
                if similarity >= threshold:
                    matched_bullets_map[bullet_text] = max(
                        matched_bullets_map.get(bullet_text, 0),
                        similarity
                    )
        
        # Calculate scores
        coverage = self._calculate_coverage(results, threshold)
        skill_match = self._calculate_skill_match(matched_bullets_map, threshold)
        seniority = self._calculate_seniority_alignment(job, matched_bullets_map)
        
        # Weighted fit score
        weights = self.matcher_config.get("weights", {})
        fit_score = (
            weights.get("required_coverage", 0.60) * coverage +
            weights.get("skill_match", 0.25) * skill_match +
            weights.get("seniority_alignment", 0.15) * seniority
        ) * 100
        
        return {
            "fit_score": round(fit_score, 1),
            "matched_bullets": [
                {"text": text, "similarity": round(sim, 3)}
                for text, sim in sorted(matched_bullets_map.items(), key=lambda x: x[1], reverse=True)
            ],
            "coverage": round(coverage * 100, 1),
            "skill_match": round(skill_match * 100, 1),
            "seniority_alignment": round(seniority * 100, 1),
            "requirements_analyzed": len(requirements)
        }
    
    def _calculate_coverage(self, search_results: List[List[Dict]], threshold: float) -> float:
        """Calculate percentage of requirements covered by resume"""
        covered = sum(
            1 for matches in search_results
            if any(m["similarity"] >= threshold for m in matches)
        )
        return covered / len(search_results) if search_results else 0
    
    def _calculate_skill_match(self, matched_bullets: Dict[str, float], threshold: float) -> float:
        """Calculate skill match strength based on similarity scores"""
        if not matched_bullets:
            return 0
        
        avg_similarity = sum(matched_bullets.values()) / len(matched_bullets)
        normalized = (avg_similarity - threshold) / (1.0 - threshold)
        return max(0, min(1, normalized))
    
    def _calculate_seniority_alignment(self, job: Dict, matched_bullets: Dict[str, float]) -> float:
        """Calculate if experience level matches job seniority"""
        job_text = (job.get("title", "") + " " + job.get("description", "")).lower()
        
        is_junior = any(kw in job_text for kw in ["junior", "entry", "intern", "new grad"])
        is_senior = any(kw in job_text for kw in ["senior", "lead", "architect", "principal"])
        
        resume_text = " ".join(matched_bullets.keys()).lower()
        leadership_count = sum(
            1 for kw in ["led", "managed", "architected", "designed", "mentored"]
            if kw in resume_text
        )
        
        if is_junior:
            return 0.8 if leadership_count <= 1 else 0.5
        elif is_senior:
            return min(1.0, 0.5 + (leadership_count * 0.15))
        return 0.7
    
    def batch_analyze(self, jobs: List[Dict]) -> List[Dict]:
        """Analyze multiple jobs and return sorted by fit score"""
        results = []
        
        for i, job in enumerate(jobs, 1):
            print(f"📊 Analyzing job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
            match_result = self.analyze_match(job)
            results.append({"job": job, "match": match_result})
        
        results.sort(key=lambda x: x["match"]["fit_score"], reverse=True)
        return results
