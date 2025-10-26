"""
Simple test suite for the agent system.
Tests the core functionality of each agent type.
"""

import unittest
import os
from unittest.mock import patch
from modules.agents import AgentFactory


class TestAgents(unittest.TestCase):
    """Test agent creation and basic functionality."""

    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_gemini_key',
        'GROQ_API_KEY': 'test_groq_key'
    })
    def test_agent_creation(self):
        """Test that all agents can be created."""
        factory = AgentFactory()
        
        cover_letter_agent = factory.get_cover_letter_agent()
        keyword_agent = factory.get_keyword_extractor_agent()
        classifier_agent = factory.get_document_classifier_agent()
        
        self.assertIsNotNone(cover_letter_agent)
        self.assertIsNotNone(keyword_agent)
        self.assertIsNotNone(classifier_agent)

    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_gemini_key',
        'GROQ_API_KEY': 'test_groq_key'
    })
    @patch('modules.agents.KeywordExtractorAgent._call_llm')
    def test_extract_technologies(self, mock_call):
        """Test technology extraction."""
        mock_call.return_value = "Python, React, AWS"
        
        factory = AgentFactory()
        agent = factory.get_keyword_extractor_agent()
        result = agent.extract_technologies("Python developer with React and AWS")
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_gemini_key',
        'GROQ_API_KEY': 'test_groq_key'
    })
    @patch('modules.agents.DocumentClassifierAgent._call_llm')
    def test_document_classification(self, mock_call):
        """Test document classification."""
        mock_call.return_value = "YES"
        
        factory = AgentFactory()
        agent = factory.get_document_classifier_agent()
        result = agent.detect_additional_documents("Please upload transcript")
        
        self.assertTrue(result)

    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_gemini_key',
        'GROQ_API_KEY': 'test_groq_key'
    })
    @patch('modules.agents.CoverLetterAgent._call_llm')
    def test_cover_letter_generation(self, mock_call):
        """Test cover letter generation."""
        mock_call.return_value = "Dear Hiring Manager, I am excited to apply..."
        
        factory = AgentFactory()
        agent = factory.get_cover_letter_agent()
        result = agent.generate_cover_letter(
            resume_text="Software Engineer",
            job_description="Python developer",
            company_name="TechCorp"
        )
        
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == '__main__':
    unittest.main()
