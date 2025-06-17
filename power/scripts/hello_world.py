#!/usr/bin/env python3
"""
Hello World Script

A production-ready hello world implementation demonstrating best practices
for Python development including proper logging, error handling, and
command-line interface.

Author: Claude Code
Version: 1.0.0
"""

import argparse
import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def generate_greeting(name: Optional[str] = None, language: str = "en") -> str:
    """
    Generate a greeting message in the specified language.

    Args:
        name: Optional name to include in greeting
        language: Language code for greeting (en, es, fr, de)

    Returns:
        Formatted greeting string

    Raises:
        ValueError: If unsupported language is provided
    """
    greetings = {
        "en": "Hello, World!",
        "es": "¡Hola, Mundo!",
        "fr": "Bonjour, le Monde!",
        "de": "Hallo, Welt!"
    }

    if language not in greetings:
        raise ValueError(f"Unsupported language: {language}. "
                        f"Supported languages: {', '.join(greetings.keys())}")

    greeting = greetings[language]

    if name is not None and name.strip():
        # Replace "World" with the provided name in different languages
        replacements = {
            "en": f"Hello, {name}!",
            "es": f"¡Hola, {name}!",
            "fr": f"Bonjour, {name}!",
            "de": f"Hallo, {name}!"
        }
        greeting = replacements[language]

    return greeting


def main() -> int:
    """
    Main entry point for the hello world application.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Production-ready Hello World script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Basic hello world
  %(prog)s --name Alice             # Personalized greeting
  %(prog)s --language es            # Spanish greeting
  %(prog)s --name Bob --language fr # French personalized greeting
  %(prog)s --verbose                # Enable debug logging
        """
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Name to include in the greeting"
    )

    parser.add_argument(
        "--language",
        choices=["en", "es", "fr", "de"],
        default="en",
        help="Language for the greeting (default: en)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    try:
        args = parser.parse_args()

        # Setup logging
        log_level = "DEBUG" if args.verbose else "INFO"
        setup_logging(log_level)

        logger = logging.getLogger(__name__)
        logger.debug("Starting hello world application")
        logger.debug("Arguments: name=%s, language=%s", args.name, args.language)

        # Generate and display greeting
        greeting = generate_greeting(args.name, args.language)
        print(greeting)

        logger.debug("Hello world application completed successfully")
        return 0

    except ValueError as error:
        logging.error("Invalid input: %s", error)
        return 1
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        return 1
    except (OSError, RuntimeError) as error:
        logging.error("System error: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
