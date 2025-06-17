#!/usr/bin/env python3
"""
Comprehensive tests for hello_world.py script.

This module provides complete test coverage for the hello world implementation,
including unit tests, integration tests, and edge case validation.
"""

import io
import logging
import sys
import unittest.mock
from unittest.mock import patch

import pytest

# Add scripts directory to path for importing
sys.path.insert(0, '/home/ikino/dev/power/scripts')
from hello_world import generate_greeting, setup_logging, main


class TestGenerateGreeting:
    """Test cases for the generate_greeting function."""
    
    def test_default_greeting(self):
        """Test default English greeting without name."""
        result = generate_greeting()
        assert result == "Hello, World!"
    
    def test_greeting_with_name(self):
        """Test personalized greeting in English."""
        result = generate_greeting(name="Alice")
        assert result == "Hello, Alice!"
    
    def test_spanish_greeting(self):
        """Test Spanish greeting without name."""
        result = generate_greeting(language="es")
        assert result == "¡Hola, Mundo!"
    
    def test_spanish_greeting_with_name(self):
        """Test personalized Spanish greeting."""
        result = generate_greeting(name="Carlos", language="es")
        assert result == "¡Hola, Carlos!"
    
    def test_french_greeting(self):
        """Test French greeting without name."""
        result = generate_greeting(language="fr")
        assert result == "Bonjour, le Monde!"
    
    def test_french_greeting_with_name(self):
        """Test personalized French greeting."""
        result = generate_greeting(name="Marie", language="fr")
        assert result == "Bonjour, Marie!"
    
    def test_german_greeting(self):
        """Test German greeting without name."""
        result = generate_greeting(language="de")
        assert result == "Hallo, Welt!"
    
    def test_german_greeting_with_name(self):
        """Test personalized German greeting."""
        result = generate_greeting(name="Hans", language="de")
        assert result == "Hallo, Hans!"
    
    def test_invalid_language(self):
        """Test error handling for unsupported language."""
        with pytest.raises(ValueError) as exc_info:
            generate_greeting(language="invalid")
        
        assert "Unsupported language: invalid" in str(exc_info.value)
        assert "Supported languages: en, es, fr, de" in str(exc_info.value)
    
    def test_empty_name(self):
        """Test handling of empty string as name."""
        result = generate_greeting(name="")
        assert result == "Hello, World!"
    
    def test_whitespace_only_name(self):
        """Test handling of whitespace-only string as name."""
        result = generate_greeting(name="   ")
        assert result == "Hello, World!"
    
    def test_special_characters_in_name(self):
        """Test handling of special characters in name."""
        result = generate_greeting(name="José-María")
        assert result == "Hello, José-María!"


class TestSetupLogging:
    """Test cases for the setup_logging function."""
    
    @patch('logging.basicConfig')
    def test_default_logging_setup(self, mock_basic_config):
        """Test default logging configuration."""
        setup_logging()
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == logging.INFO
        assert '%(asctime)s - %(name)s - %(levelname)s - %(message)s' in call_args[1]['format']
    
    @patch('logging.basicConfig')
    def test_debug_logging_setup(self, mock_basic_config):
        """Test debug logging configuration."""
        setup_logging("DEBUG")
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == logging.DEBUG
    
    @patch('logging.basicConfig')
    def test_error_logging_setup(self, mock_basic_config):
        """Test error logging configuration."""
        setup_logging("ERROR")
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == logging.ERROR
    
    @patch('logging.basicConfig')
    def test_case_insensitive_log_level(self, mock_basic_config):
        """Test case insensitive log level handling."""
        setup_logging("info")
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == logging.INFO


class TestMainFunction:
    """Test cases for the main function."""
    
    @patch('sys.argv', ['hello_world.py'])
    @patch('builtins.print')
    def test_main_default_execution(self, mock_print):
        """Test main function with default arguments."""
        result = main()
        
        assert result == 0
        mock_print.assert_called_once_with("Hello, World!")
    
    @patch('sys.argv', ['hello_world.py', '--name', 'Alice'])
    @patch('builtins.print')
    def test_main_with_name(self, mock_print):
        """Test main function with name argument."""
        result = main()
        
        assert result == 0
        mock_print.assert_called_once_with("Hello, Alice!")
    
    @patch('sys.argv', ['hello_world.py', '--language', 'es'])
    @patch('builtins.print')
    def test_main_with_language(self, mock_print):
        """Test main function with language argument."""
        result = main()
        
        assert result == 0
        mock_print.assert_called_once_with("¡Hola, Mundo!")
    
    @patch('sys.argv', ['hello_world.py', '--name', 'Carlos', '--language', 'es'])
    @patch('builtins.print')
    def test_main_with_name_and_language(self, mock_print):
        """Test main function with both name and language arguments."""
        result = main()
        
        assert result == 0
        mock_print.assert_called_once_with("¡Hola, Carlos!")
    
    @patch('sys.argv', ['hello_world.py'])
    @patch('hello_world.generate_greeting')
    @patch('logging.error')
    def test_main_invalid_language_error(self, mock_log_error, mock_generate_greeting):
        """Test main function error handling for invalid language in generate_greeting."""
        mock_generate_greeting.side_effect = ValueError("Unsupported language: invalid")
        result = main()
        
        assert result == 1
        mock_log_error.assert_called_once()
        assert "Invalid input:" in mock_log_error.call_args[0][0]
    
    @patch('sys.argv', ['hello_world.py', '--verbose'])
    @patch('builtins.print')
    @patch('hello_world.setup_logging')
    def test_main_verbose_mode(self, mock_setup_logging, mock_print):
        """Test main function with verbose flag."""
        result = main()
        
        assert result == 0
        mock_setup_logging.assert_called_once_with("DEBUG")
        mock_print.assert_called_once_with("Hello, World!")
    
    @patch('sys.argv', ['hello_world.py'])
    @patch('hello_world.generate_greeting')
    def test_main_keyboard_interrupt(self, mock_generate_greeting):
        """Test main function handling of KeyboardInterrupt."""
        mock_generate_greeting.side_effect = KeyboardInterrupt()
        
        with patch('logging.info') as mock_log_info:
            result = main()
        
        assert result == 1
        mock_log_info.assert_called_once_with("Application interrupted by user")
    
    @patch('sys.argv', ['hello_world.py'])
    @patch('hello_world.generate_greeting')
    def test_main_unexpected_exception(self, mock_generate_greeting):
        """Test main function handling of unexpected exceptions."""
        mock_generate_greeting.side_effect = RuntimeError("Unexpected error")
        
        with patch('logging.error') as mock_log_error:
            result = main()
        
        assert result == 1
        mock_log_error.assert_called_once()
        assert "System error:" in mock_log_error.call_args[0][0]


class TestCommandLineInterface:
    """Integration tests for command line interface."""
    
    def test_help_output(self, capsys):
        """Test help message output."""
        with patch('sys.argv', ['hello_world.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Production-ready Hello World script" in captured.out
            assert "Examples:" in captured.out
    
    def test_version_output(self, capsys):
        """Test version output."""
        with patch('sys.argv', ['hello_world.py', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "1.0.0" in captured.out
    
    def test_invalid_language_choice(self, capsys):
        """Test invalid language choice handling."""
        with patch('sys.argv', ['hello_world.py', '--language', 'invalid']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # argparse error exit code
            captured = capsys.readouterr()
            assert "invalid choice" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=hello_world", "--cov-report=term-missing"])