"""Unit tests for Filter Engine"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.filters import FilterEngine, FilterDecision


class TestFilterEngine:
    """Test job filtering logic"""
    
    def test_batch_filter_by_score_threshold(self):
        """Test filtering by minimum score threshold"""
        config = {
            "matcher": {
                "min_match_score": 50
            }
        }
        
        engine = FilterEngine(config)
        
        results = [
            {"job": {"id": "1", "title": "Job 1"}, "match": {"fit_score": 60}},
            {"job": {"id": "2", "title": "Job 2"}, "match": {"fit_score": 40}},
            {"job": {"id": "3", "title": "Job 3"}, "match": {"fit_score": 75}}
        ]
        
        filtered = engine.apply_batch(results)
        
        assert len(filtered) == 2
        assert filtered[0]["job"]["id"] == "1"
        assert filtered[1]["job"]["id"] == "3"
    
    def test_batch_filter_by_location(self):
        """Test filtering by preferred locations"""
        config = {
            "preferred_locations": ["Toronto", "Remote"],
            "matcher": {"min_match_score": 0}
        }
        
        engine = FilterEngine(config)
        
        results = [
            {"job": {"id": "1", "location": "Toronto, ON"}, "match": {"fit_score": 80}},
            {"job": {"id": "2", "location": "Vancouver, BC"}, "match": {"fit_score": 80}},
            {"job": {"id": "3", "location": "Remote"}, "match": {"fit_score": 80}}
        ]
        
        filtered = engine.apply_batch(results)
        
        assert len(filtered) == 2
        assert filtered[0]["job"]["id"] == "1"
        assert filtered[1]["job"]["id"] == "3"
    
    def test_batch_filter_avoid_companies(self):
        """Test filtering out companies to avoid"""
        config = {
            "companies_to_avoid": ["BadCorp", "AvoidMe"],
            "matcher": {"min_match_score": 0}
        }
        
        engine = FilterEngine(config)
        
        results = [
            {"job": {"id": "1", "company": "GoodCorp"}, "match": {"fit_score": 80}},
            {"job": {"id": "2", "company": "BadCorp Inc"}, "match": {"fit_score": 80}},
            {"job": {"id": "3", "company": "TechCo"}, "match": {"fit_score": 80}}
        ]
        
        filtered = engine.apply_batch(results)
        
        assert len(filtered) == 2
        assert filtered[0]["job"]["id"] == "1"
        assert filtered[1]["job"]["id"] == "3"
    
    def test_batch_filter_by_keywords(self):
        """Test filtering by required keywords"""
        config = {
            "keywords_to_match": ["python", "react"],
            "matcher": {"min_match_score": 0}
        }
        
        engine = FilterEngine(config)
        
        results = [
            {"job": {"id": "1", "title": "Python Developer", "skills": "Python, Django"}, "match": {"fit_score": 80}},
            {"job": {"id": "2", "title": "Java Developer", "skills": "Java, Spring"}, "match": {"fit_score": 80}},
            {"job": {"id": "3", "title": "React Developer", "skills": "React, TypeScript"}, "match": {"fit_score": 80}}
        ]
        
        filtered = engine.apply_batch(results)
        
        assert len(filtered) == 2
        assert filtered[0]["job"]["id"] == "1"
        assert filtered[1]["job"]["id"] == "3"
    
    def test_realtime_decision_auto_save(self):
        """Test real-time decision for auto-save"""
        config = {
            "matcher": {
                "auto_save_threshold": 80,
                "min_match_score": 50
            }
        }
        
        engine = FilterEngine(config)
        
        job = {"id": "1", "title": "High Score Job"}
        match = {"fit_score": 85}
        
        decision = engine.decide_realtime(job, match, auto_save_enabled=True)
        
        assert decision.auto_save is True
        assert decision.skip is False
    
    def test_realtime_decision_no_auto_save_when_disabled(self):
        """Test that auto-save doesn't trigger when disabled"""
        config = {
            "matcher": {
                "auto_save_threshold": 80,
                "min_match_score": 50
            }
        }
        
        engine = FilterEngine(config)
        
        job = {"id": "1", "title": "High Score Job"}
        match = {"fit_score": 85}
        
        decision = engine.decide_realtime(job, match, auto_save_enabled=False)
        
        assert decision.auto_save is False
        assert decision.skip is False
    
    def test_empty_config_uses_defaults(self):
        """Test that empty config uses default values"""
        engine = FilterEngine({})
        
        assert engine.min_score == 0
        assert engine.auto_save_threshold == 30
        assert engine.preferred_locations == []
        assert engine.keywords == []
        assert engine.avoid_companies == []


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
