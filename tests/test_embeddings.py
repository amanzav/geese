"""
Test script for embeddings module
Tests embedding generation and FAISS search
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.embeddings import EmbeddingsManager


def test_embeddings():
    print("🧪 Testing Embeddings Module\n")
    
    # Sample resume bullets
    resume_bullets = [
        "Built React Native onboarding flow with TypeScript, app linking, and secure token storage using Keychain/Keystore",
        "Integrated Android NDK C++ module into React Native via TurboModules to expose low-level APIs",
        "Owned CI/CD with Fastlane; managed TestFlight and Play Console staged rollouts",
        "Developed REST API with Node.js, Express, PostgreSQL; achieved <50ms p95 latency",
        "Led migration from MongoDB to PostgreSQL for improved data consistency and query performance",
        "Implemented WebSocket real-time chat feature handling 10K+ concurrent connections",
        "Built data pipeline using Python, Apache Airflow, and AWS Lambda for ETL processing",
        "Designed and deployed microservices architecture on AWS ECS with Docker containers"
    ]
    
    # Sample job requirements (queries)
    job_bullets = [
        "Experience with React Native mobile development",
        "Strong backend API development skills with Node.js",
        "Cloud infrastructure experience (AWS, Docker, Kubernetes)",
        "Experience with GraphQL and modern frontend frameworks"
    ]
    
    print("=" * 60)
    print("TEST 1: Initialize Embeddings Manager")
    print("=" * 60 + "\n")
    
    embeddings = EmbeddingsManager()
    print()
    
    print("=" * 60)
    print("TEST 2: Build Resume Index")
    print("=" * 60 + "\n")
    
    embeddings.build_resume_index(resume_bullets)
    print()
    
    print("=" * 60)
    print("TEST 3: Search for Similar Resume Bullets")
    print("=" * 60 + "\n")
    
    results = embeddings.search(job_bullets, k=3)
    
    for i, (query, matches) in enumerate(zip(job_bullets, results), 1):
        print(f"\nQuery {i}: {query}\n")
        print("Top 3 Matches:")
        for rank, match in enumerate(matches, 1):
            sim = match['similarity']
            bullet = match['resume_bullet']
            # Truncate long bullets
            if len(bullet) > 80:
                bullet = bullet[:77] + "..."
            
            # Color code similarity
            if sim >= 0.65:
                status = "✓ MATCH"
            elif sim >= 0.50:
                status = "⚠ WEAK"
            else:
                status = "✗ LOW"
            
            print(f"  {rank}. [{status}] Sim: {sim:.3f}")
            print(f"     {bullet}")
        print()
    
    print("=" * 60)
    print("TEST 4: Load Index from Cache")
    print("=" * 60 + "\n")
    
    # Create new instance and load from cache
    embeddings2 = EmbeddingsManager()
    if embeddings2.index_exists():
        embeddings2.load_index()
        print("✅ Successfully loaded cached index\n")
        
        # Verify it works
        test_query = ["Python data pipeline experience"]
        test_results = embeddings2.search(test_query, k=1)
        print(f"Test query: {test_query[0]}")
        print(f"Best match: {test_results[0][0]['resume_bullet']}")
        print(f"Similarity: {test_results[0][0]['similarity']:.3f}")
    else:
        print("⚠️  No cached index found")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_embeddings()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
