"""Unit tests for WaterlooWorks authentication with simplified mocking"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWaterlooWorksAuth:
    """Test authentication logic with mocked Selenium"""
    
    @patch('modules.auth.webdriver.Chrome')
    @patch('modules.auth.WebDriverWait')
    def test_login_sequence(self, mock_wait, mock_chrome):
        """Test that login performs correct sequence of actions"""
        # Mock driver and elements
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock elements
        mock_username_input = Mock()
        mock_next_button = Mock()
        mock_password_input = Mock()
        mock_submit_button = Mock()
        mock_trust_button = Mock()
        mock_header = Mock()
        
        elements = {
            ("id", "userNameInput"): mock_username_input,
            ("id", "nextButton"): mock_next_button,
            ("id", "passwordInput"): mock_password_input,
            ("id", "submitButton"): mock_submit_button,
            ("id", "trust-browser-button"): mock_trust_button,
            ("xpath", '//h1[text()="WaterlooWorks"]'): mock_header
        }
        
        mock_driver.find_element.side_effect = lambda by, value: elements.get((by, value), Mock())
        
        # Mock WebDriverWait to return elements immediately
        mock_wait.return_value.until.side_effect = lambda condition: condition(mock_driver)
        
        from modules.auth import WaterlooWorksAuth
        
        auth = WaterlooWorksAuth("test@waterloo.ca", "password123")
        auth.login()
        
        # Verify login sequence
        mock_driver.get.assert_called_with("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
        mock_username_input.send_keys.assert_called_with("test@waterloo.ca")
        mock_next_button.click.assert_called_once()
        mock_password_input.send_keys.assert_called_with("password123")
        mock_submit_button.click.assert_called_once()
        mock_trust_button.click.assert_called_once()
    
    def test_close_does_not_quit_injected_driver(self):
        """Test that close() doesn't quit an injected driver"""
        mock_driver = Mock()
        
        from modules.auth import WaterlooWorksAuth
        
        auth = WaterlooWorksAuth("test@waterloo.ca", "password123", driver=mock_driver)
        auth.close()
        
        mock_driver.quit.assert_not_called()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
