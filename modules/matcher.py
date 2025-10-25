"""
Resume Matcher - Matches job descriptions to resume using embeddings
"""

import json
import os
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

try:  # Optional dependency for environments running tests without PDF parsing
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled in _extract_bullets_from_pdf
    PdfReader = None

from modules.config import AppConfig, load_app_config
from modules.services import MatcherResourceService, get_matcher_service

if TYPE_CHECKING:  # pragma: no cover - only for static typing
    from modules.embeddings import EmbeddingsManager


class ResumeMatcher:
    """Analyzes job descriptions against resume to calculate match scores"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        *,
        config_path: str = "config.json",
        cache_path: Optional[str] = None,
        resume_bullets: Optional[List[str]] = None,
        embeddings_manager: Optional["EmbeddingsManager"] = None,
        resources: Optional[MatcherResourceService] = None,
    ):
        """Initialize matcher with configuration and shared resources."""

        self.config = config or load_app_config(config_path)
        self.matcher_config = self.config.matcher

        if resources is None:
            resources = get_matcher_service(
                self.config,
                cache_path=cache_path or "data/job_matches_cache.json",
            )
        elif cache_path:
            resources.cache_path = cache_path

        if resume_bullets is not None:
            resources.set_resume_bullets(resume_bullets)
        if embeddings_manager is not None:
            resources.set_embeddings_manager(embeddings_manager)

        self.resources = resources
        self.cache_path = self.resources.cache_path
        self.resume_cache_path = self.resources.resume_cache_path

        self._resume_index_prepared = False

        # Load match cache via shared service
        self.match_cache = self._load_match_cache()
        print(f"📦 Loaded {len(self.match_cache)} cached job matches\n")
    
    def _read_match_cache_from_disk(self) -> Dict[str, Dict]:
        """Load cached match results from disk"""
        if not self.cache_path or self.cache_path == ":memory:":
            return {}

        if not os.path.exists(self.cache_path):
            return {}

        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading match cache: {e}")
            return {}

    def _load_match_cache(self) -> Dict[str, Dict]:
        if self.resources:
            return self.resources.provide_match_cache(self._read_match_cache_from_disk)
        return self._read_match_cache_from_disk()

    def _save_match_cache(self):
        """Save match cache to disk"""
        try:
            dirpath = os.path.dirname(self.cache_path) if self.cache_path else ""
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)
            if self.cache_path and self.cache_path != ":memory:":
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.match_cache, f, indent=2, ensure_ascii=False)
            if self.resources:
                self.resources.update_match_cache(self.match_cache)
        except Exception as e:
            print(f"⚠️  Error saving match cache: {e}")
    
    def _get_cached_match(self, job_id: str) -> Optional[Dict]:
        """Get cached match result for a job ID"""
        return self.match_cache.get(job_id)

    def _cache_match(self, job_id: str, match_result: Dict):
        """Cache a match result"""
        match_result["last_updated"] = datetime.now().isoformat()
        self.match_cache[job_id] = match_result

    def _load_resume(self) -> List[str]:
        """Load resume from cached text file or PDF, including skills section"""
        cached_path = self.resume_cache_path

        if cached_path and cached_path != ":memory:" and os.path.exists(cached_path):
            print(f"📄 Loading resume from {cached_path}")
            with open(cached_path, 'r', encoding='utf-8') as f:
                bullets = [line.strip() for line in f if line.strip()]

            # Add explicit skills as pseudo-bullets for better matching
            # This ensures technologies mentioned in skills section but not in bullets are indexed
            skills_bullets = self._get_skills_bullets()
            if skills_bullets:
                print(f"📋 Adding {len(skills_bullets)} skill entries from skills section")
                bullets.extend(skills_bullets)

            return bullets

        # Extract from PDF if no cache
        resume_path = self.config.resume_path
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")

        print(f"📄 Extracting text from {resume_path}")
        bullets = self._extract_bullets_from_pdf(resume_path)

        # Cache for future use (bullets only, skills added separately)
        if cached_path and cached_path != ":memory:":
            cache_dir = os.path.dirname(cached_path)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            with open(cached_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(bullets))

        # Add skills
        skills_bullets = self._get_skills_bullets()
        if skills_bullets:
            print(f"📋 Adding {len(skills_bullets)} skill entries from skills section")
            bullets.extend(skills_bullets)

        return bullets

    def _get_resume_bullets(self) -> List[str]:
        """Return resume bullets, loading from disk if necessary."""
        return self.resources.provide_resume_bullets(self._load_resume)

    def _create_embeddings_manager(self) -> "EmbeddingsManager":
        from modules.embeddings import EmbeddingsManager  # Local import to avoid heavy dependency unless needed

        model_name = self.matcher_config.get("embedding_model")
        return EmbeddingsManager(model_name=model_name)

    def _get_embeddings_manager(self) -> "EmbeddingsManager":
        return self.resources.provide_embeddings(self._create_embeddings_manager)

    def _prepare_embeddings(self) -> "EmbeddingsManager":
        embeddings = self._get_embeddings_manager()
        if not self._resume_index_prepared:
            resume_bullets = self._get_resume_bullets()
            if embeddings.index_exists():
                print("📂 Loading cached resume embeddings...")
                embeddings.load_index()
                if getattr(embeddings, "resume_bullets", None):
                    self.resources.set_resume_bullets(embeddings.resume_bullets)
            else:
                print("🔨 Building resume embeddings...")
                embeddings.build_resume_index(resume_bullets)

            print(f"✅ Resume loaded with {len(self._get_resume_bullets())} bullets\n")
            self._resume_index_prepared = True

        return embeddings
    
    def _get_skills_bullets(self) -> List[str]:
        """
        Generate pseudo-bullets from explicit skills section.
        This ensures technologies in skills but not in experience bullets are still indexed.
        """
        # Read from config or hardcoded skills
        skills_config = self.config.explicit_skills
        
        if not skills_config:
            # Fallback: try to extract from PDF or use default
            return []
        
        skills_bullets = []
        
        # Convert skill categories into searchable bullets
        for category, skills in skills_config.items():
            if isinstance(skills, list):
                # Create a bullet per skill for better granularity
                for skill in skills:
                    skills_bullets.append(f"Proficient in {skill}")
            elif isinstance(skills, str):
                # If it's a comma-separated string
                skill_list = [s.strip() for s in skills.split(',')]
                for skill in skill_list:
                    skills_bullets.append(f"Proficient in {skill}")
        
        return skills_bullets
    
    def _extract_bullets_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract bullet points from resume PDF"""
        if PdfReader is None:
            raise ImportError("pypdf is required to extract resume text")

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
    
    def _extract_technologies(self, text: str) -> set:
        """Extract technology keywords from text using regex patterns"""
        if not text:
            return set()
        
        import re
        
        # Comprehensive tech keyword list with canonical names
        # NOTE: Process in order - C++/C# before C to avoid false matches
        tech_patterns = [
            # Languages - Order matters!
            ('C++', r'c\+\+'),  # No \b as it doesn't work with +
            ('C#', r'c#'),  # No \b as it doesn't work with #
            ('Python', r'\bpython\b'),
            ('Java', r'\bjava\b(?!script)'),  # Java but not JavaScript
            ('JavaScript', r'\bjavascript\b'),
            ('TypeScript', r'\b(typescript|ts)\b'),
            ('Go', r'\b(golang|go)\b'),
            ('Rust', r'\brust\b'),
            ('Kotlin', r'\bkotlin\b'),
            ('Swift', r'\bswift\b'),
            ('Ruby', r'\bruby\b'),
            ('PHP', r'\bphp\b'),
            ('Scala', r'\bscala\b'),
            ('R', r'\b(r language|\br\s)'),
            ('MATLAB', r'\bmatlab\b'),
            # C last with explicit context keywords
            ('C', r'\b(c language|c programming\b|c developer\b|(?<!\w)c\b(?=\s+(and|or|language|programming|developer|engineer|code)))'),
            
            # Frontend Frameworks
            ('React Native', r'\breact[\s-]native\b'),
            ('React', r'\breact(\.js)?\b'),
            ('Vue', r'\bvue(\.js)?\b'),
            ('Angular', r'\bangular\b'),
            ('Next.js', r'\bnext(\.js)?\b'),
            ('Svelte', r'\bsvelte\b'),
            ('jQuery', r'\bjquery\b'),
            ('Bootstrap', r'\bbootstrap\b'),
            ('Tailwind CSS', r'\btailwind( css)?\b'),
            
            # Backend Frameworks
            ('Node.js', r'\bnode(\.js)?\b'),
            ('Django', r'\bdjango\b'),
            ('Flask', r'\bflask\b'),
            ('FastAPI', r'\bfastapi\b'),
            ('Spring', r'\bspring( boot| framework)?\b'),
            ('Express', r'\bexpress(\.js)?\b'),
            ('NestJS', r'\bnest(\.js)?\b'),
            ('Rails', r'\bruby on rails|rails\b'),
            
            # Mobile
            ('Flutter', r'\bflutter\b'),
            ('iOS', r'\bios\b'),
            ('Android', r'\bandroid\b'),
            
            # Cloud & DevOps
            ('AWS', r'\baws|amazon web services\b'),
            ('Azure', r'\bazure|microsoft azure\b'),
            ('GCP', r'\bgcp|google cloud\b'),
            ('Lambda', r'\b(aws )?lambda\b'),
            ('S3', r'\bs3\b'),
            ('EC2', r'\bec2\b'),
            ('Kubernetes', r'\bkubernetes|k8s\b'),
            ('Docker', r'\bdocker\b'),
            ('Terraform', r'\bterraform\b'),
            ('Ansible', r'\bansible\b'),
            ('Jenkins', r'\bjenkins\b'),
            ('CI/CD', r'\bci/cd|ci\/cd\b'),
            ('GitHub Actions', r'\bgithub actions\b'),
            ('GitLab', r'\bgitlab( ci)?\b'),
            ('CircleCI', r'\bcircleci\b'),
            
            # Databases
            ('PostgreSQL', r'\bpostgresql|postgres\b'),
            ('MySQL', r'\bmysql\b'),
            ('MongoDB', r'\bmongodb|mongo\b'),
            ('Redis', r'\bredis\b'),
            ('DynamoDB', r'\bdynamodb\b'),
            ('Cassandra', r'\bcassandra\b'),
            ('Elasticsearch', r'\belasticsearch|elastic search\b'),
            ('SQL', r'\bsql\b'),
            ('NoSQL', r'\bnosql\b'),
            ('SQLite', r'\bsqlite\b'),
            
            # ML/AI
            ('TensorFlow', r'\btensorflow\b'),
            ('PyTorch', r'\bpytorch\b'),
            ('Keras', r'\bkeras\b'),
            ('Scikit-learn', r'\bscikit-learn|sklearn\b'),
            ('LangChain', r'\blangchain\b'),
            ('LLM', r'\bllm|large language model\b'),
            ('Transformers', r'\btransformers\b'),
            ('OpenAI', r'\bopenai\b'),
            ('Hugging Face', r'\bhugging ?face\b'),
            ('BERT', r'\bbert\b'),
            ('GPT', r'\bgpt\b'),
            ('Machine Learning', r'\bmachine learning|ml\b'),
            ('Deep Learning', r'\bdeep learning\b'),
            ('NLP', r'\bnlp|natural language processing\b'),
            
            # Data
            ('Pandas', r'\bpandas\b'),
            ('NumPy', r'\bnumpy\b'),
            ('Spark', r'\bspark|apache spark\b'),
            ('Airflow', r'\bairflow\b'),
            ('Kafka', r'\bkafka|apache kafka\b'),
            ('Hadoop', r'\bhadoop\b'),
            ('Tableau', r'\btableau\b'),
            ('Power BI', r'\bpower ?bi\b'),
            
            # Tools & Others
            ('Git', r'\bgit\b'),
            ('Linux', r'\blinux\b'),
            ('Bash', r'\bbash\b'),
            ('Unix', r'\bunix\b'),
            ('Agile', r'\bagile\b'),
            ('Scrum', r'\bscrum\b'),
            ('REST API', r'\brest(ful)? api\b'),
            ('GraphQL', r'\bgraphql\b'),
            ('gRPC', r'\bgrpc\b'),
            ('WebSocket', r'\bwebsocket\b'),
            ('MQTT', r'\bmqtt\b'),
            ('Selenium', r'\bselenium\b'),
            ('Pytest', r'\bpytest\b'),
            ('Jest', r'\bjest\b'),
            ('JUnit', r'\bjunit\b')
        ]
        
        text_lower = text.lower()
        found_techs = set()
        
        # Process patterns in order
        for canonical_name, pattern in tech_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_techs.add(canonical_name)
        
        return found_techs
    
    def _parse_job_to_requirements(self, job: Dict) -> Dict[str, List[str]]:
        """Extract structured requirements from job with priority levels"""
        requirements = {
            "must_have_skills": [],
            "nice_to_have_skills": [],
            "responsibilities": [],
            "all_requirements": []  # For semantic search
        }
        
        # Common generic phrases to skip (pure fluff with no semantic value)
        SKIP_PHRASES = [
            "strong communication", "excellent communication", "good communication",
            "team player", "strong work ethic", "attention to detail",
            "problem solving", "time management", "organizational skills",
            "interpersonal skills", "written communication", "verbal communication",
            "strong motivation", "self-motivated", "quick learner",
            "quality and achieving deadlines", "commitment to quality",
            "strong technical writing", "technical writing skills",
            "work independently", "work in a team", "fast-paced environment"
        ]
        
        def is_meaningful_requirement(text: str) -> bool:
            """Check if requirement is meaningful (not generic fluff)"""
            text_lower = text.lower()
            
            # Skip if contains generic phrases
            if any(phrase in text_lower for phrase in SKIP_PHRASES):
                return False
            
            # Skip if it's just "Experience in [role] role" (redundant)
            if text_lower.startswith("experience in") and "role" in text_lower:
                return False
            
            # Must contain at least one technical keyword or be action-oriented
            has_tech = any(tech in text_lower for tech in [
                "python", "java", "c++", "javascript", "react", "sql", "api",
                "develop", "build", "design", "implement", "architect", "deploy",
                "debug", "test", "optimize", "integrate", "maintain", "engineer",
                "database", "cloud", "aws", "azure", "docker", "kubernetes",
                "git", "agile", "scrum", "linux", "windows", "web", "mobile"
            ])
            
            return has_tech
        
        # Extract from skills section
        skills_text = job.get("skills", "")
        if skills_text and skills_text != "N/A":
            # Split by newlines and filter meaningful lines
            for line in skills_text.split('\n'):
                line = line.strip()
                
                # Skip headers, very short lines, and bullets
                if (len(line) < 15 or 
                    line.endswith(':') or
                    line.lower().startswith(('required', 'preferred', 'qualifications', 'skills', 'what we'))):
                    continue
                
                # Remove leading bullet symbols
                for symbol in ['•', '●', '◦', '▪', '-', '*', '–']:
                    if line.startswith(symbol):
                        line = line[1:].strip()
                        break
                
                if len(line) < 15:  # Recheck after removing bullet
                    continue
                
                # Skip if not meaningful
                if not is_meaningful_requirement(line):
                    continue
                
                line_lower = line.lower()
                
                # Nice-to-have indicators (prioritize these first)
                if any(kw in line_lower for kw in [
                    "nice to have", "nice-to-have", "bonus", "preferred", 
                    "plus", "asset", "would be", "a plus"
                ]):
                    requirements["nice_to_have_skills"].append(line)
                # Must-have indicators or general skills
                else:
                    requirements["must_have_skills"].append(line)
        
        # Extract from responsibilities
        resp_text = job.get("responsibilities", "")
        if resp_text and resp_text != "N/A":
            for line in resp_text.split('\n'):
                line = line.strip()
                
                # Skip headers
                if (line.endswith(':') or 
                    line.lower().startswith(('responsibilities', 'what you', 'you will', 'duties'))):
                    continue
                
                # Remove bullets
                for symbol in ['•', '●', '◦', '▪', '-', '*', '–']:
                    if line.startswith(symbol):
                        line = line[1:].strip()
                        break
                
                if len(line) > 20 and is_meaningful_requirement(line):
                    requirements["responsibilities"].append(line)
        
        # Extract key sentences from summary
        summary_text = job.get("summary", "")
        if summary_text and summary_text != "N/A":
            # Split into sentences
            sentences = []
            for sent in summary_text.replace('!', '.').replace('?', '.').split('.'):
                sent = sent.strip()
                # Look for action-oriented sentences with keywords
                if (len(sent) > 30 and is_meaningful_requirement(sent) and
                    any(kw in sent.lower() for kw in [
                        'will', 'looking for', 'seeking', 'experience', 
                        'work', 'build', 'develop', 'design', 'create'
                    ])):
                    sentences.append(sent)
            
            requirements["responsibilities"].extend(sentences[:3])
        
        # Combine all for semantic search (prioritize must-haves)
        requirements["all_requirements"] = (
            requirements["must_have_skills"][:10] +   # Top 10 must-haves
            requirements["responsibilities"][:5] +    # Top 5 responsibilities  
            requirements["nice_to_have_skills"][:3]   # Top 3 nice-to-haves
        )
        
        return requirements
    
    def analyze_match(self, job: Dict) -> Dict:
        """Analyze how well resume matches a job using hybrid approach"""
        requirements = self._parse_job_to_requirements(job)

        if not requirements["all_requirements"]:
            return {
                "fit_score": 0,
                "matched_bullets": [],
                "coverage": 0,
                "skill_match": 0,
                "keyword_match": 0,
                "seniority_alignment": 50,
                "matched_technologies": [],
                "missing_technologies": [],
                "error": "No requirements found in job"
            }

        embeddings = self._prepare_embeddings()
        resume_bullets = self._get_resume_bullets()

        # 1. KEYWORD MATCHING (Explicit technology match)
        job_text = " ".join([
            job.get('summary', ''),
            job.get('responsibilities', ''),
            job.get('skills', '')
        ])
        job_techs = self._extract_technologies(job_text)

        resume_text = " ".join(resume_bullets)
        resume_techs = self._extract_technologies(resume_text)

        # Calculate keyword overlap
        matched_techs = job_techs & resume_techs
        keyword_overlap = len(matched_techs) / len(job_techs) if job_techs else 0
        
        # 2. SEMANTIC SEARCH (Contextual understanding)
        top_k = self.matcher_config.get("top_k", 5)
        threshold = self.matcher_config.get("similarity_threshold", 0.30)  # Tuned for technical text matching

        # Search with all requirements
        results = embeddings.search(requirements["all_requirements"], k=top_k)

        # Collect unique matched bullets
        matched_bullets_map = {}
        for req_matches in results:
            for match in req_matches:
                bullet_text = resume_bullets[match["index"]]
                similarity = match["similarity"]

                if similarity >= threshold:
                    matched_bullets_map[bullet_text] = max(
                        matched_bullets_map.get(bullet_text, 0),
                        similarity
                    )
        
        # Calculate semantic scores
        semantic_coverage = self._calculate_coverage(results, threshold)
        semantic_strength = self._calculate_skill_match(matched_bullets_map, threshold)
        seniority = self._calculate_seniority_alignment(job, matched_bullets_map)
        
        # 3. MUST-HAVE PENALTY
        # Check how many must-have skills are not found in resume
        must_haves = requirements["must_have_skills"]
        missing_must_haves = 0
        
        if must_haves:
            # Search for must-haves specifically
            must_have_results = embeddings.search(must_haves, k=top_k)
            for req_matches in must_have_results:
                # If no match above threshold, it's missing
                if not any(m["similarity"] >= threshold for m in req_matches):
                    missing_must_haves += 1
        
        # Apply penalty: 5% per missing must-have skill
        penalty_per_missing = self.matcher_config.get("penalty_per_missing_must_have", 0.05)
        must_have_penalty = missing_must_haves * penalty_per_missing
        
        # 4. HYBRID WEIGHTED SCORE
        # Balance between explicit tech match and contextual fit
        weights = self.matcher_config.get("weights", {})
        fit_score = (
            weights.get("keyword_match", 0.35) * keyword_overlap +      # 35% explicit tech
            weights.get("semantic_coverage", 0.40) * semantic_coverage + # 40% requirement coverage
            weights.get("semantic_strength", 0.10) * semantic_strength + # 10% match quality
            weights.get("seniority_alignment", 0.15) * seniority         # 15% experience level
        ) * 100
        
        # Apply must-have penalty
        fit_score = max(0, fit_score - (must_have_penalty * 100))
        
        return {
            "fit_score": round(fit_score, 1),
            "matched_bullets": [
                {"text": text, "similarity": round(sim, 3)}
                for text, sim in sorted(matched_bullets_map.items(), key=lambda x: x[1], reverse=True)
            ],
            "coverage": round(semantic_coverage * 100, 1),
            "skill_match": round(semantic_strength * 100, 1),
            "keyword_match": round(keyword_overlap * 100, 1),
            "seniority_alignment": round(seniority * 100, 1),
            "requirements_analyzed": len(requirements["all_requirements"]),
            "must_have_skills": len(must_haves),
            "missing_must_haves": missing_must_haves,
            "must_have_penalty": round(must_have_penalty * 100, 1),
            "matched_technologies": sorted(list(matched_techs)),
            "missing_technologies": sorted(list(job_techs - resume_techs)),
            "total_technologies_required": len(job_techs)
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
        # Combine all text fields for analysis
        job_text_parts = []
        for field in ['title', 'level', 'summary', 'responsibilities', 'skills', 'work_term_duration']:
            if job.get(field) and job[field] != 'N/A':
                job_text_parts.append(job[field])
        job_text = " ".join(job_text_parts).lower()
        
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
    
    def analyze_single_job(self, job: Dict, use_cache: bool = True) -> Dict:
        """
        Analyze a single job and return result (used for real-time processing)
        
        Args:
            job: Job dictionary to analyze
            use_cache: If True, check cache first
        
        Returns:
            Dictionary with job and match data
        """
        job_id = job.get('id', 'unknown')
        
        # Check cache first
        if use_cache:
            cached_match = self._get_cached_match(job_id)
            if cached_match:
                return {"job": job, "match": cached_match}
        
        # Calculate new match
        match_result = self.analyze_match(job)
        
        # Cache the result
        self._cache_match(job_id, match_result)
        self._save_match_cache()  # Save immediately for real-time mode
        
        return {"job": job, "match": match_result}
    
    def batch_analyze(self, jobs: List[Dict], force_rematch: bool = False) -> List[Dict]:
        """
        Analyze multiple jobs and return sorted by fit score
        
        Args:
            jobs: List of job dictionaries to analyze
            force_rematch: If True, ignore cache and recalculate all matches
        
        Returns:
            List of results with job and match data, sorted by fit score
        """
        results = []
        cached_count = 0
        new_count = 0
        
        for i, job in enumerate(jobs, 1):
            job_id = job.get('id', f'job_{i}')
            job_title = job.get('title', 'Unknown')
            
            # Check cache first (unless force_rematch is True)
            if not force_rematch:
                cached_match = self._get_cached_match(job_id)
                if cached_match:
                    print(f"✓ [{i}/{len(jobs)}] Using cached match for: {job_title}")
                    results.append({"job": job, "match": cached_match})
                    cached_count += 1
                    continue
            
            # Calculate new match
            print(f"🔍 [{i}/{len(jobs)}] Analyzing: {job_title}")
            match_result = self.analyze_match(job)
            
            # Cache the result
            self._cache_match(job_id, match_result)
            
            results.append({"job": job, "match": match_result})
            new_count += 1
        
        # Save cache after processing all jobs
        if new_count > 0:
            self._save_match_cache()
            print(f"\n💾 Saved {new_count} new matches to cache")
        
        if cached_count > 0:
            print(f"📦 Used {cached_count} cached matches")
        
        results.sort(key=lambda x: x["match"]["fit_score"], reverse=True)
        return results
