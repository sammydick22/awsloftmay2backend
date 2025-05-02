#!/usr/bin/env python3
"""
Test runner for the Outbound Sales Prospector backend.

This script discovers and runs all tests in the tests directory.
It can be run from the command line:

    python run_tests.py

Or with specific test patterns:

    python run_tests.py test_api.py
    python run_tests.py test_api.py:TestFlaskAPI.test_state_endpoint_no_leads
"""

import os
import sys
import unittest
import argparse


def discover_and_run_tests(pattern=None):
    """
    Discover and run tests based on the optional pattern.
    
    Args:
        pattern: Optional test pattern to filter tests.
    """
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    if pattern:
        test_loader = unittest.TestLoader()
        
        if ':' in pattern:
            # Handle specific test case or method: test_file.py:TestClass.test_method
            file_path, test_spec = pattern.split(':', 1)
            
            # Check if it's a file.py:TestClass or file.py:TestClass.test_method
            if '.' in test_spec:
                test_class, test_method = test_spec.split('.', 1)
                suite = test_loader.loadTestsFromName(f"tests.{file_path.replace('.py', '')}.{test_class}.{test_method}")
            else:
                suite = test_loader.loadTestsFromName(f"tests.{file_path.replace('.py', '')}.{test_spec}")
        else:
            # Handle specific test file: test_file.py
            suite = test_loader.discover('tests', pattern=pattern)
    else:
        # Discover all tests in the tests directory
        suite = unittest.defaultTestLoader.discover('tests')
    
    # Create a test runner and run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return the exit code based on the test result
    return 0 if result.wasSuccessful() else 1


def main():
    """Parse command line arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run tests for the Outbound Sales Prospector backend.')
    parser.add_argument('pattern', nargs='?', help='Optional pattern to filter tests (e.g., test_api.py or test_api.py:TestFlaskAPI.test_state_endpoint_no_leads)')
    args = parser.parse_args()
    
    # Call the test discovery and runner
    sys.exit(discover_and_run_tests(args.pattern))


if __name__ == '__main__':
    main()
