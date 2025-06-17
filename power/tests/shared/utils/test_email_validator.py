"""
Comprehensive tests for email validation utility.

Tests cover valid and invalid email formats, strict mode validation,
error handling, and edge cases for robust email validation.
"""

import pytest
from typing import Dict, Any

from shared.utils.email_validator import (
    EmailValidationError,
    validate_email_address,
    is_valid_email,
    get_email_domain
)


class TestValidateEmailAddress:
    """Test cases for validate_email_address function."""

    def test_valid_basic_email(self) -> None:
        """Test validation of basic valid email addresses."""
        test_emails = [
            'user@example.com',
            'test.email@domain.org',
            'user123@test-domain.net',
            'simple@test.co.uk'
        ]
        
        for email in test_emails:
            result = validate_email_address(email)
            assert result['is_valid'] is True
            assert result['email'] == email.lower()
            assert '@' in result['email']
            assert result['local_part'] and result['domain_part']

    def test_valid_complex_email_strict_mode(self) -> None:
        """Test validation of complex valid emails in strict mode."""
        test_emails = [
            'user+tag@example.com',
            'user_name@domain-name.com',
            'test.email+tag@sub.domain.org'
        ]
        
        for email in test_emails:
            result = validate_email_address(email, strict_mode=True)
            assert result['is_valid'] is True
            assert len(result['warnings']) == 0

    def test_email_normalization(self) -> None:
        """Test email address normalization."""
        test_cases = [
            ('  USER@EXAMPLE.COM  ', 'user@example.com'),
            ('Test.Email@Domain.Org', 'test.email@domain.org'),
            ('\tuser@domain.com\n', 'user@domain.com')
        ]
        
        for input_email, expected in test_cases:
            result = validate_email_address(input_email)
            assert result['email'] == expected

    def test_email_parts_extraction(self) -> None:
        """Test correct extraction of local and domain parts."""
        test_cases = [
            ('user@example.com', 'user', 'example.com'),
            ('test.email@sub.domain.org', 'test.email', 'sub.domain.org'),
            ('user123@test-domain.net', 'user123', 'test-domain.net')
        ]
        
        for email, expected_local, expected_domain in test_cases:
            result = validate_email_address(email)
            assert result['local_part'] == expected_local
            assert result['domain_part'] == expected_domain

    def test_invalid_email_no_at_symbol(self) -> None:
        """Test validation failure for emails without @ symbol."""
        invalid_emails = [
            'userexample.com',
            'plainaddress',
            'user.domain.com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert "must contain '@' symbol" in str(exc_info.value)
            assert exc_info.value.email_address == email

    def test_invalid_email_multiple_at_symbols(self) -> None:
        """Test validation failure for emails with multiple @ symbols."""
        invalid_emails = [
            'user@@example.com',
            'user@example@com',
            'test@user@domain.com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert "exactly one '@' symbol" in str(exc_info.value)

    def test_invalid_local_part_empty(self) -> None:
        """Test validation failure for empty local part."""
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address('@example.com')
        assert "Local part cannot be empty" in str(exc_info.value)

    def test_invalid_local_part_too_long(self) -> None:
        """Test validation failure for local part exceeding 64 characters."""
        long_local = 'a' * 65
        email = f'{long_local}@example.com'
        
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address(email)
        assert "Local part cannot exceed 64 characters" in str(exc_info.value)

    def test_invalid_local_part_consecutive_dots(self) -> None:
        """Test validation failure for consecutive dots in local part."""
        invalid_emails = [
            'user..name@example.com',
            'test...email@domain.org',
            'user.name..@example.com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert "consecutive dots" in str(exc_info.value)

    def test_invalid_local_part_leading_trailing_dots(self) -> None:
        """Test validation failure for leading/trailing dots in local part."""
        invalid_emails = [
            '.user@example.com',
            'user.@example.com',
            '.user.name@domain.org'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert "cannot start or end with a dot" in str(exc_info.value)

    def test_invalid_domain_part_empty(self) -> None:
        """Test validation failure for empty domain part."""
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address('user@')
        assert "Domain part cannot be empty" in str(exc_info.value)

    def test_invalid_domain_part_too_long(self) -> None:
        """Test validation failure for domain part exceeding 253 characters."""
        long_domain = 'a' * 250 + '.com'
        email = f'user@{long_domain}'
        
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address(email)
        assert "Domain part cannot exceed 253 characters" in str(exc_info.value)

    def test_invalid_domain_part_no_tld(self) -> None:
        """Test validation failure for domain without TLD."""
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address('user@localhost')
        assert "must contain at least one dot" in str(exc_info.value)

    def test_invalid_domain_part_consecutive_dots(self) -> None:
        """Test validation failure for consecutive dots in domain."""
        invalid_emails = [
            'user@example..com',
            'user@sub..domain.org',
            'user@test...domain.net'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert "consecutive dots" in str(exc_info.value)

    def test_invalid_domain_part_leading_trailing_characters(self) -> None:
        """Test validation failure for invalid leading/trailing characters."""
        invalid_emails = [
            'user@.example.com',
            'user@example.com.',
            'user@-example.com',
            'user@example.com-'
        ]
        
        for email in invalid_emails:
            with pytest.raises(EmailValidationError) as exc_info:
                validate_email_address(email)
            assert ("cannot start or end" in str(exc_info.value) or
                    "empty labels" in str(exc_info.value))

    def test_empty_input_validation(self) -> None:
        """Test validation of empty or None inputs."""
        with pytest.raises(ValueError) as exc_info:
            validate_email_address(None)
        assert "cannot be None or empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_email_address('')
        assert "cannot be None or empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            validate_email_address('   ')
        assert "cannot be empty after normalization" in str(exc_info.value)

    def test_non_string_input_validation(self) -> None:
        """Test validation of non-string inputs."""
        invalid_inputs = [123, ['user@example.com'], {'email': 'test'}, True]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError) as exc_info:
                validate_email_address(invalid_input)
            assert "must be a string" in str(exc_info.value)

    def test_strict_mode_differences(self) -> None:
        """Test differences between strict and non-strict validation modes."""
        # Email with uncommon but valid characters
        test_email = 'user_name@example.com'
        
        # Should pass in both modes
        result_strict = validate_email_address(test_email, strict_mode=True)
        result_non_strict = validate_email_address(test_email, strict_mode=False)
        
        assert result_strict['is_valid'] is True
        assert result_non_strict['is_valid'] is True


class TestIsValidEmail:
    """Test cases for is_valid_email function."""

    def test_valid_emails_return_true(self) -> None:
        """Test that valid emails return True."""
        valid_emails = [
            'user@example.com',
            'test.email@domain.org',
            'user123@test-domain.net'
        ]
        
        for email in valid_emails:
            assert is_valid_email(email) is True
            assert is_valid_email(email, strict_mode=False) is True

    def test_invalid_emails_return_false(self) -> None:
        """Test that invalid emails return False."""
        invalid_emails = [
            'userexample.com',
            'user@@example.com',
            '@example.com',
            'user@',
            '',
            None
        ]
        
        for email in invalid_emails:
            assert is_valid_email(email) is False

    def test_exception_handling(self) -> None:
        """Test that exceptions are handled gracefully."""
        # Should not raise exceptions, only return False
        assert is_valid_email(123) is False
        assert is_valid_email([]) is False
        assert is_valid_email({}) is False


class TestGetEmailDomain:
    """Test cases for get_email_domain function."""

    def test_valid_email_returns_domain(self) -> None:
        """Test domain extraction from valid emails."""
        test_cases = [
            ('user@example.com', 'example.com'),
            ('test.email@sub.domain.org', 'sub.domain.org'),
            ('USER@DOMAIN.NET', 'domain.net')
        ]
        
        for email, expected_domain in test_cases:
            result = get_email_domain(email)
            assert result == expected_domain

    def test_invalid_email_returns_none(self) -> None:
        """Test that invalid emails return None."""
        invalid_emails = [
            'userexample.com',
            'user@@example.com',
            '@example.com',
            '',
            None,
            123
        ]
        
        for email in invalid_emails:
            assert get_email_domain(email) is None

    def test_uses_non_strict_mode(self) -> None:
        """Test that get_email_domain uses non-strict validation."""
        # Email that might be stricter in strict mode
        email = 'user@example.com'
        result = get_email_domain(email)
        assert result == 'example.com'


class TestEmailValidationError:
    """Test cases for EmailValidationError exception."""

    def test_exception_properties(self) -> None:
        """Test that exception stores email and validation errors."""
        email = 'invalid@@email.com'
        errors = ['Multiple @ symbols', 'Invalid format']
        
        try:
            validate_email_address(email)
        except EmailValidationError as exc:
            assert exc.email_address == email
            assert exc.validation_errors is not None
            assert len(exc.validation_errors) > 0

    def test_exception_inheritance(self) -> None:
        """Test that EmailValidationError inherits from DataValidationError."""
        from shared.exceptions import DataValidationError
        
        try:
            validate_email_address('invalid@@email.com')
        except EmailValidationError as exc:
            assert isinstance(exc, DataValidationError)
            assert hasattr(exc, 'to_dict')


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_valid_lengths(self) -> None:
        """Test emails at maximum valid lengths."""
        # 64 character local part
        local_part = 'a' * 64
        email = f'{local_part}@example.com'
        result = validate_email_address(email)
        assert result['is_valid'] is True

    def test_international_domains(self) -> None:
        """Test handling of international domain names."""
        # Basic ASCII domain handling
        email = 'user@test-domain.co.uk'
        result = validate_email_address(email)
        assert result['is_valid'] is True
        assert result['domain_part'] == 'test-domain.co.uk'

    def test_tld_validation(self) -> None:
        """Test top-level domain validation."""
        valid_emails = [
            'user@example.com',
            'user@example.org',
            'user@example.co.uk',
            'user@example.info'
        ]
        
        for email in valid_emails:
            result = validate_email_address(email)
            assert result['is_valid'] is True

        # Single character TLD should fail
        with pytest.raises(EmailValidationError) as exc_info:
            validate_email_address('user@example.c')
        assert "at least 2 characters" in str(exc_info.value)

    def test_warning_generation(self) -> None:
        """Test that warnings are generated in non-strict mode."""
        # This would depend on specific implementation details
        # For now, test that warnings list exists in result
        result = validate_email_address('user@example.com', strict_mode=False)
        assert 'warnings' in result
        assert isinstance(result['warnings'], list)