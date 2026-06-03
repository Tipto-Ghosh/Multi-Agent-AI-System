"""
Tests for MCP server tools and resources.

These tests call the tool functions DIRECTLY as Python functions.
not through the MCP protocol. This is intentional:

1. Speed, no subprocess startup, no stdio piping overhead
2. Isolation, tests the logic, not the transport
3. Debuggability, stack traces point directly to the function

In production, the MCP transport (stdio or HTTP) is tested
separately via integration tests. For unit testing, calling
the functions directly is the right pattern.

Run: uv run -m pytest tests/test_mcp_servers.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from src.logger import logging
from src.exception import LearningAcceleratorException
from src.mcp_servers.filesystem_server import (
    list_study_files,
    read_study_file,
    search_notes,
    get_notes_index,
    NOTES_BASE,
)
from src.mcp_servers.memory_server import (
    memory_set,
    memory_get,
    memory_list_keys,
    memory_delete,
    get_session_summary,
    _store,   # direct access for test cleanup
)


logging.info("=" * 20)
logging.info("MCP Server Test Suite Initialized")
logging.info(f"NOTES_BASE path: {NOTES_BASE}")
logging.info(f"Memory store initialized with {len(_store)} sessions")
logging.info("=" * 20)


# Filesystem server tests
class TestListStudyFiles:
    """Tests for the list_study_files tool."""

    def test_returns_list(self):
        """Should always return a list, even if empty."""
        logging.info("Starting test_returns_list - verifying list_study_files returns a list")
        
        try:
            result = list_study_files()
            
            logging.info(f"list_study_files returned {len(result)} files")
            
            assert isinstance(result, list), f"Expected list, got {type(result).__name__}"
            
            logging.info("test_returns_list passed - list_study_files returns a list")
            
        except AssertionError as e:
            logging.error(f"Type assertion failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_list: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_finds_sample_notes(self):
        """Should find the three sample note files from Batch 1."""
        logging.info("Starting test_finds_sample_notes - verifying sample note files exist")
        
        try:
            result = list_study_files()
            
            logging.info(f"Found {len(result)} .md files: {result[:5]}...")
            
            assert len(result) >= 1, (
                "No .md files found. Make sure study_materials/sample_notes/ "
                "contains the files created in Batch 1."
            )
            
            logging.info(f"test_finds_sample_notes passed - found {len(result)} sample note files")
            
        except AssertionError as e:
            logging.error(f"No sample notes found: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_finds_sample_notes: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_returns_only_md_files(self):
        """All returned files should end in .md."""
        logging.info("Starting test_returns_only_md_files - verifying file extensions")
        
        try:
            result = list_study_files()
            
            logging.info(f"Checking {len(result)} files for .md extension")
            
            for filename in result:
                if not filename.endswith(".md"):
                    logging.error(f"Non-.md file found: {filename}")
                    raise AssertionError(f"Non-.md file returned: {filename}")
            
            logging.info(f"test_returns_only_md_files passed - all {len(result)} files are .md")
            
        except AssertionError as e:
            logging.error(f"File extension validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_only_md_files: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_results_are_sorted(self):
        """Results should be in alphabetical order."""
        logging.info("Starting test_results_are_sorted - verifying alphabetical sorting")
        
        try:
            result = list_study_files()
            
            logging.info(f"Checking sort order for {len(result)} files")
            logging.info(f"First 3 files: {result[:3] if len(result) >= 3 else result}")
            
            sorted_result = sorted(result)
            if result != sorted_result:
                logging.error(f"Files are not sorted alphabetically")
                logging.error(f"Actual order: {result}")
                logging.error(f"Expected order: {sorted_result}")
            
            assert result == sorted_result, "Files are not in alphabetical order"
            
            logging.info("test_results_are_sorted passed - files are alphabetically sorted")
            
        except AssertionError as e:
            logging.error(f"Sort order validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_results_are_sorted: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_returns_relative_paths(self):
        """Paths should be relative, not absolute."""
        logging.info("Starting test_returns_relative_paths - verifying path format")
        
        try:
            result = list_study_files()
            
            logging.info(f"Checking {len(result)} files for relative paths")
            
            for filename in result:
                if filename.startswith("/"):
                    logging.error(f"Absolute path found: {filename}")
                    raise AssertionError(f"Absolute path returned: {filename}")
            
            logging.info(f"test_returns_relative_paths passed - all {len(result)} paths are relative")
            
        except AssertionError as e:
            logging.error(f"Path format validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_relative_paths: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestReadStudyFile:
    """Tests for the read_study_file tool."""

    def test_reads_existing_file(self):
        """Should return file content for a known file."""
        logging.info("Starting test_reads_existing_file - testing file reading")
        
        try:
            files = list_study_files()
            logging.info(f"Available files: {files}")
            
            if not files:
                logging.warning("No study files available, skipping test")
                pytest.skip("No study files available")
            
            target_file = files[0]
            logging.info(f"Attempting to read file: {target_file}")
            
            content = read_study_file(target_file)
            
            logging.info(f"Read {len(content)} characters from {target_file}")
            
            assert isinstance(content, str), f"Expected string, got {type(content).__name__}"
            assert len(content) > 0, "File content is empty"
            assert not content.startswith("Error:"), f"Error reading file: {content[:100]}"
            
            logging.info("test_reads_existing_file passed - successfully read file content")
            
        except AssertionError as e:
            logging.error(f"File reading assertion failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_reads_existing_file: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_closures_file_contains_expected_content(self):
        """The closures.md file should contain closure-related content."""
        logging.info("Starting test_closures_file_contains_expected_content")
        
        try:
            logging.info("Reading closures.md content")
            content = read_study_file("closures.md")
            
            logging.info(f"Checking if content contains 'closure' keyword")
            contains_closure = "closure" in content.lower()
            logging.info(f"Content contains 'closure': {contains_closure}")
            
            assert "closure" in content.lower(), (
                "closures.md doesn't contain 'closure', check the file content"
            )
            
            logging.info("test_closures_file_contains_expected_content passed")
            
        except AssertionError as e:
            logging.error(f"Content validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_closures_file_contains_expected_content: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_nonexistent_file_returns_error_string(self):
        """Missing files should return error string, not raise exception."""
        logging.info("Starting test_nonexistent_file_returns_error_string")
        
        try:
            nonexistent_file = "does_not_exist.md"
            logging.info(f"Attempting to read nonexistent file: {nonexistent_file}")
            
            result = read_study_file(nonexistent_file)
            
            logging.info(f"Result for nonexistent file: {result[:100]}")
            
            assert result.startswith("Error:"), f"Expected error string, got: {result[:50]}"
            assert "not found" in result, f"Expected 'not found' in error, got: {result[:100]}"
            
            logging.info("test_nonexistent_file_returns_error_string passed")
            
        except AssertionError as e:
            logging.error(f"Error handling validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_nonexistent_file_returns_error_string: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_path_traversal_blocked(self):
        """Path traversal attempts should return error string."""
        logging.info("Starting test_path_traversal_blocked - security check")
        
        try:
            traversal_path = "../../.env"
            logging.info(f"Attempting path traversal with: {traversal_path}")
            
            result = read_study_file(traversal_path)
            
            logging.info(f"Path traversal result: {result[:100]}")
            
            assert result.startswith("Error:"), f"Expected error string, got: {result[:50]}"
            assert "traversal" in result.lower(), f"Expected 'traversal' warning, got: {result[:100]}"
            
            logging.info("test_path_traversal_blocked passed - security check working")
            
        except AssertionError as e:
            logging.error(f"Path traversal security check failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_path_traversal_blocked: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_non_md_file_blocked(self):
        """Non-.md files should return error string."""
        logging.info("Starting test_non_md_file_blocked - file extension check")
        
        try:
            non_md_file = "requirements.txt"
            logging.info(f"Attempting to read non-.md file: {non_md_file}")
            
            result = read_study_file(non_md_file)
            
            logging.info(f"Non-.md file result: {result[:100]}")
            
            assert result.startswith("Error:"), f"Expected error string, got: {result[:50]}"
            
            logging.info("test_non_md_file_blocked passed - non-.md files blocked")
            
        except AssertionError as e:
            logging.error(f"File extension blocking failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_non_md_file_blocked: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_returns_string_not_bytes(self):
        """Content should be decoded string, not bytes."""
        logging.info("Starting test_returns_string_not_bytes - type checking")
        
        try:
            files = list_study_files()
            
            if not files:
                logging.warning("No study files available, skipping test")
                pytest.skip("No study files available")
            
            target_file = files[0]
            logging.info(f"Reading file for type check: {target_file}")
            
            content = read_study_file(target_file)
            
            logging.info(f"Content type: {type(content).__name__}, length: {len(content)}")
            
            assert isinstance(content, str), f"Expected str, got {type(content).__name__}"
            
            logging.info("test_returns_string_not_bytes passed - returns string type")
            
        except AssertionError as e:
            logging.error(f"Type validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_string_not_bytes: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestSearchNotes:
    """Tests for the search_notes tool."""

    def test_returns_list(self):
        """Should always return a list."""
        logging.info("Starting test_returns_list - verifying search_notes returns list")
        
        try:
            result = search_notes("python")
            
            logging.info(f"search_notes('python') returned {len(result)} results")
            
            assert isinstance(result, list), f"Expected list, got {type(result).__name__}"
            
            logging.info("test_returns_list passed - search_notes returns a list")
            
        except AssertionError as e:
            logging.error(f"Type assertion failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_list: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_finds_known_term(self):
        """Searching for 'closure' should find results in closures.md."""
        logging.info("Starting test_finds_known_term - searching for 'closure'")
        
        try:
            results = search_notes("closure")
            
            logging.info(f"Found {len(results)} results for 'closure'")
            
            if len(results) > 0:
                logging.info(f"First result: {results[0]}")
            
            assert len(results) > 0, (
                "No results for 'closure', check closures.md exists and contains this term"
            )
            
            logging.info("test_finds_known_term passed - found closure-related content")
            
        except AssertionError as e:
            logging.error(f"Search result validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_finds_known_term: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_result_has_required_keys(self):
        """Each result should have file, line_number, and line keys."""
        logging.info("Starting test_result_has_required_keys - validating result structure")
        
        try:
            results = search_notes("def")
            logging.info(f"Found {len(results)} results for 'def'")
            
            if not results:
                logging.warning("No results found for 'def', skipping test")
                pytest.skip("No results found for 'def'")
            
            for i, result in enumerate(results[:3]):  # Log first 3 results
                logging.info(f"Result {i}: keys={list(result.keys())}")
            
            for result in results:
                missing_keys = [key for key in ["file", "line_number", "line"] if key not in result]
                if missing_keys:
                    logging.error(f"Result missing keys: {missing_keys}")
                    raise AssertionError(f"Missing required keys: {missing_keys}")
            
            logging.info(f"test_result_has_required_keys passed - all {len(results)} results have required keys")
            
        except AssertionError as e:
            logging.error(f"Result structure validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_result_has_required_keys: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_line_numbers_are_positive_integers(self):
        """Line numbers should be 1-based positive integers."""
        logging.info("Starting test_line_numbers_are_positive_integers")
        
        try:
            results = search_notes("python")
            logging.info(f"Found {len(results)} results for 'python'")
            
            invalid_lines = []
            for result in results:
                line_num = result["line_number"]
                if not isinstance(line_num, int) or line_num < 1:
                    invalid_lines.append(line_num)
                    logging.error(f"Invalid line number found: {line_num}")
            
            if invalid_lines:
                raise AssertionError(f"Invalid line numbers found: {invalid_lines}")
            
            logging.info(f"test_line_numbers_are_positive_integers passed - all line numbers valid")
            
        except AssertionError as e:
            logging.error(f"Line number validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_line_numbers_are_positive_integers: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_case_insensitive_search(self):
        """Search should be case-insensitive."""
        logging.info("Starting test_case_insensitive_search")
        
        try:
            upper = search_notes("CLOSURE")
            lower = search_notes("closure")
            mixed = search_notes("Closure")
            
            logging.info(f"Results: UPPER={len(upper)}, lower={len(lower)}, Mixed={len(mixed)}")
            
            # All should return the same number of results
            assert len(upper) == len(lower) == len(mixed), (
                f"Case sensitivity issue: UPPER={len(upper)}, lower={len(lower)}, Mixed={len(mixed)}"
            )
            
            logging.info("test_case_insensitive_search passed - search is case-insensitive")
            
        except AssertionError as e:
            logging.error(f"Case sensitivity validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_case_insensitive_search: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_max_results_is_20(self):
        """Search should return at most 20 results."""
        logging.info("Starting test_max_results_is_20 - checking result limit")
        
        try:
            results = search_notes("e")
            
            logging.info(f"Search for 'e' returned {len(results)} results")
            
            assert len(results) <= 20, f"Expected at most 20 results, got {len(results)}"
            
            logging.info("test_max_results_is_20 passed - results capped at 20")
            
        except AssertionError as e:
            logging.error(f"Result limit validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_max_results_is_20: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_no_match_returns_empty_list(self):
        """Searching for gibberish should return empty list, not error."""
        logging.info("Starting test_no_match_returns_empty_list")
        
        try:
            search_term = "xyzzy_impossible_string_12345"
            logging.info(f"Searching for nonexistent term: '{search_term}'")
            
            results = search_notes(search_term)
            
            logging.info(f"No-match search returned {len(results)} results")
            
            assert results == [], f"Expected empty list, got {len(results)} results"
            
            logging.info("test_no_match_returns_empty_list passed - returns empty list")
            
        except AssertionError as e:
            logging.error(f"No-match handling failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_no_match_returns_empty_list: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestGetNotesIndex:
    """Tests for the notes://index resource."""

    def test_returns_string(self):
        """Should return a string."""
        logging.info("Starting test_returns_string - verifying get_notes_index returns string")
        
        try:
            result = get_notes_index()
            
            logging.info(f"get_notes_index returned {len(result)} characters")
            
            assert isinstance(result, str), f"Expected string, got {type(result).__name__}"
            
            logging.info("test_returns_string passed - returns string type")
            
        except AssertionError as e:
            logging.error(f"Type validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_returns_string: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_contains_markdown_header(self):
        """Should contain the markdown header for study materials index."""
        logging.info("Starting test_contains_markdown_header")
        
        try:
            result = get_notes_index()
            
            contains_header = "# Study Materials Index" in result
            logging.info(f"Contains markdown header: {contains_header}")
            
            assert "# Study Materials Index" in result, "Missing expected markdown header"
            
            logging.info("test_contains_markdown_header passed")
            
        except AssertionError as e:
            logging.error(f"Markdown header validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_contains_markdown_header: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_lists_known_files(self):
        """Should list closures.md in the index."""
        logging.info("Starting test_lists_known_files - checking for closures.md")
        
        try:
            result = get_notes_index()
            
            contains_closures = "closures.md" in result
            logging.info(f"Contains closures.md: {contains_closures}")
            
            assert "closures.md" in result, "closures.md not found in notes index"
            
            logging.info("test_lists_known_files passed - closures.md listed in index")
            
        except AssertionError as e:
            logging.error(f"Known file listing failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_lists_known_files: {str(e)}")
            raise LearningAcceleratorException(e, sys)


# Memory server tests
class TestMemoryServer:
    """Tests for memory_set, memory_get, memory_list_keys, memory_delete."""

    def setup_method(self):
        """Clear the store before each test for isolation."""
        logging.info(f"Setting up memory store: clearing {len(_store)} sessions")
        _store.clear()
        logging.info("Memory store cleared for test isolation")

    def teardown_method(self):
        """Clear the store after each test."""
        logging.info(f"Tearing down: clearing memory store ({len(_store)} sessions)")
        _store.clear()
        logging.info("Memory store cleared after test")

    def test_set_and_get_simple_value(self):
        """Basic round-trip: set a value and get it back."""
        logging.info("Starting test_set_and_get_simple_value")
        
        try:
            session_id = "session-1"
            key = "goal"
            value = "Learn Python closures"
            
            logging.info(f"Setting memory: session='{session_id}', key='{key}', value='{value}'")
            memory_set(session_id, key, value)
            
            result = memory_get(session_id, key)
            logging.info(f"Retrieved value: '{result}'")
            
            assert result == value, f"Expected '{value}', got '{result}'"
            
            logging.info("test_set_and_get_simple_value passed")
            
        except AssertionError as e:
            logging.error(f"Memory round-trip failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_set_and_get_simple_value: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_missing_key_returns_null_string(self):
        """Getting a key that doesn't exist should return 'null', not raise."""
        logging.info("Starting test_get_missing_key_returns_null_string")
        
        try:
            session_id = "session-1"
            key = "nonexistent_key"
            
            logging.info(f"Getting nonexistent key: session='{session_id}', key='{key}'")
            result = memory_get(session_id, key)
            
            logging.info(f"Result for missing key: '{result}'")
            
            assert result == "null", f"Expected 'null', got '{result}'"
            
            logging.info("test_get_missing_key_returns_null_string passed")
            
        except AssertionError as e:
            logging.error(f"Missing key handling failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_get_missing_key_returns_null_string: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_missing_session_returns_null(self):
        """Getting from a session that doesn't exist should return 'null'."""
        logging.info("Starting test_get_missing_session_returns_null")
        
        try:
            session_id = "session-never-created"
            
            logging.info(f"Getting from nonexistent session: '{session_id}'")
            result = memory_get(session_id, "any_key")
            
            logging.info(f"Result for missing session: '{result}'")
            
            assert result == "null", f"Expected 'null', got '{result}'"
            
            logging.info("test_get_missing_session_returns_null passed")
            
        except AssertionError as e:
            logging.error(f"Missing session handling failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_get_missing_session_returns_null: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_sessions_are_isolated(self):
        """Data stored in session-1 should not appear in session-2."""
        logging.info("Starting test_sessions_are_isolated")
        
        try:
            session_1 = "session-1"
            session_2 = "session-2"
            key = "key"
            value_1 = "value-for-session-1"
            
            logging.info(f"Setting {key}='{value_1}' in {session_1}")
            memory_set(session_1, key, value_1)
            
            logging.info(f"Getting {key} from {session_2}")
            result = memory_get(session_2, key)
            
            logging.info(f"Result from {session_2}: '{result}'")
            
            assert result == "null", f"Expected 'null' (session isolation), got '{result}'"
            
            logging.info("test_sessions_are_isolated passed - sessions are properly isolated")
            
        except AssertionError as e:
            logging.error(f"Session isolation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_sessions_are_isolated: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_overwrite_existing_value(self):
        """Setting the same key twice should update to the new value."""
        logging.info("Starting test_overwrite_existing_value")
        
        try:
            session_id = "session-1"
            key = "score"
            
            logging.info(f"Setting initial value: {key}='0.6'")
            memory_set(session_id, key, "0.6")
            
            logging.info(f"Overwriting value: {key}='0.9'")
            memory_set(session_id, key, "0.9")
            
            result = memory_get(session_id, key)
            logging.info(f"Final value: '{result}'")
            
            assert result == "0.9", f"Expected '0.9' after overwrite, got '{result}'"
            
            logging.info("test_overwrite_existing_value passed - value was updated")
            
        except AssertionError as e:
            logging.error(f"Value overwrite failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_overwrite_existing_value: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_json_values_round_trip(self):
        """JSON-serialized complex data should survive a round trip."""
        logging.info("Starting test_json_values_round_trip")
        
        try:
            session_id = "session-1"
            key = "progress"
            data = {"topics": ["closures", "decorators"], "score": 0.85}
            
            logging.info(f"Storing JSON data: {data}")
            memory_set(session_id, key, json.dumps(data))
            
            retrieved = memory_get(session_id, key)
            logging.info(f"Retrieved JSON string: {retrieved}")
            
            parsed = json.loads(retrieved)
            logging.info(f"Parsed JSON: {parsed}")
            
            assert parsed["topics"] == ["closures", "decorators"], f"Topics mismatch: {parsed['topics']}"
            assert parsed["score"] == 0.85, f"Score mismatch: {parsed['score']}"
            
            logging.info("test_json_values_round_trip passed - JSON data preserved")
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding failed: {str(e)}")
            raise LearningAcceleratorException(f"JSON round-trip failed: {str(e)}", sys)
        except AssertionError as e:
            logging.error(f"JSON data validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_json_values_round_trip: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_list_keys_empty_for_new_session(self):
        """A session with no data should return empty key list."""
        logging.info("Starting test_list_keys_empty_for_new_session")
        
        try:
            session_id = "brand-new-session"
            
            logging.info(f"Listing keys for new session: '{session_id}'")
            result = memory_list_keys(session_id)
            
            logging.info(f"Keys returned: {result} (type: {type(result).__name__})")
            
            # Verify it's a list and it's empty
            assert isinstance(result, list), f"Expected list, got {type(result).__name__}"
            assert result == [], f"Expected empty list, got {result}"
            assert len(result) == 0, f"Expected 0 keys, got {len(result)}"
            
            logging.info("test_list_keys_empty_for_new_session passed")
            
        except AssertionError as e:
            logging.error(f"Empty session key listing failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_list_keys_empty_for_new_session: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_list_keys_returns_all_stored_keys(self):
        """list_keys should return all keys stored in the session."""
        logging.info("Starting test_list_keys_returns_all_stored_keys")
        
        try:
            session_id = "session-1"
            keys_to_store = {
                "key_a": "value_a", 
                "key_b": "value_b", 
                "key_c": "value_c"
            }
            
            for key, value in keys_to_store.items():
                logging.info(f"Setting {key}='{value}' in {session_id}")
                memory_set(session_id, key, value)
            
            keys = memory_list_keys(session_id)
            logging.info(f"Retrieved keys: {keys} (type: {type(keys).__name__})")
            
            # Verify it's a list first
            assert isinstance(keys, list), f"Expected list, got {type(keys).__name__}"
            
            # Convert to set for comparison
            actual_keys = set(keys)
            expected_keys = {"key_a", "key_b", "key_c"}
            
            assert actual_keys == expected_keys, (
                f"Expected keys {expected_keys}, got {actual_keys}"
            )
            assert len(keys) == 3, f"Expected 3 keys, got {len(keys)}"
            
            logging.info("test_list_keys_returns_all_stored_keys passed")
            
        except AssertionError as e:
            logging.error(f"Key listing validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_list_keys_returns_all_stored_keys: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        
    def test_delete_existing_key(self):
        """Deleting an existing key should make it inaccessible."""
        logging.info("Starting test_delete_existing_key")
        
        try:
            session_id = "session-1"
            key = "temp_key"
            value = "temp_value"
            
            logging.info(f"Setting and then deleting: {key}='{value}'")
            memory_set(session_id, key, value)
            memory_delete(session_id, key)
            
            result = memory_get(session_id, key)
            logging.info(f"Value after delete: '{result}'")
            
            assert result == "null", f"Expected 'null' after delete, got '{result}'"
            
            logging.info("test_delete_existing_key passed - key properly deleted")
            
        except AssertionError as e:
            logging.error(f"Key deletion failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_delete_existing_key: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_delete_nonexistent_key_does_not_raise(self):
        """Deleting a key that doesn't exist should return gracefully."""
        logging.info("Starting test_delete_nonexistent_key_does_not_raise")
        
        try:
            session_id = "session-1"
            key = "nonexistent"
            
            logging.info(f"Deleting nonexistent key: {key}")
            result = memory_delete(session_id, key)
            
            logging.info(f"Delete result: {result}")
            
            assert "not found" in result.lower(), f"Expected 'not found' in result, got: {result}"
            
            logging.info("test_delete_nonexistent_key_does_not_raise passed")
            
        except AssertionError as e:
            logging.error(f"Nonexistent key deletion handling failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_delete_nonexistent_key_does_not_raise: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_set_returns_confirmation(self):
        """memory_set should return a confirmation message string."""
        logging.info("Starting test_set_returns_confirmation")
        
        try:
            session_id = "session-1"
            key = "key"
            value = "value"
            
            logging.info(f"Calling memory_set with session='{session_id}', key='{key}', value='{value}'")
            result = memory_set(session_id, key, value)
            
            logging.info(f"Confirmation message: '{result}'")
            
            assert isinstance(result, str), f"Expected string confirmation, got {type(result).__name__}"
            assert session_id in result, f"Session ID not in confirmation: {result}"
            assert key in result, f"Key not in confirmation: {result}"
            
            logging.info("test_set_returns_confirmation passed")
            
        except AssertionError as e:
            logging.error(f"Confirmation message validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_set_returns_confirmation: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_multiple_sessions_independent(self):
        """Multiple sessions should not interfere with each other."""
        logging.info("Starting test_multiple_sessions_independent")
        
        try:
            session_count = 5
            logging.info(f"Setting up {session_count} independent sessions")
            
            for i in range(session_count):
                session_id = f"session-{i}"
                value = f"value-{i}"
                logging.info(f"Setting session '{session_id}' with value '{value}'")
                memory_set(session_id, "data", value)
            
            for i in range(session_count):
                session_id = f"session-{i}"
                expected_value = f"value-{i}"
                result = memory_get(session_id, "data")
                
                logging.info(f"Checking session '{session_id}': expected='{expected_value}', got='{result}'")
                assert result == expected_value, f"Session {session_id}: expected '{expected_value}', got '{result}'"
            
            logging.info(f"test_multiple_sessions_independent passed - {session_count} sessions verified")
            
        except AssertionError as e:
            logging.error(f"Multiple session independence failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_multiple_sessions_independent: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestGetSessionSummary:
    """Tests for the notes://session/{session_id} resource."""

    def setup_method(self):
        """Clear store before each test."""
        logging.info(f"Setting up session summary tests: clearing store ({len(_store)} sessions)")
        _store.clear()
        logging.info("Store cleared for session summary test")

    def teardown_method(self):
        """Clear store after each test."""
        logging.info(f"Tearing down session summary tests: clearing store ({len(_store)} sessions)")
        _store.clear()
        logging.info("Store cleared after session summary test")

    def test_empty_session_returns_no_data_message(self):
        """Empty session should return appropriate message."""
        logging.info("Starting test_empty_session_returns_no_data_message")
        
        try:
            session_id = "empty-session"
            
            logging.info(f"Getting summary for empty session: '{session_id}'")
            result = get_session_summary(session_id)
            
            logging.info(f"Empty session summary (first 100 chars): {result[:100]}...")
            
            assert "No data stored yet" in result, f"Expected 'No data stored yet' message, got: {result[:100]}"
            
            logging.info("test_empty_session_returns_no_data_message passed")
            
        except AssertionError as e:
            logging.error(f"Empty session message validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_empty_session_returns_no_data_message: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_populated_session_contains_keys(self):
        """Populated session summary should show stored keys."""
        logging.info("Starting test_populated_session_contains_keys")
        
        try:
            session_id = "test-session"
            
            memory_set(session_id, "explained_topics", '["closures"]')
            logging.info(f"Set explained_topics in {session_id}")
            
            memory_set(session_id, "last_score", "0.85")
            logging.info(f"Set last_score in {session_id}")
            
            result = get_session_summary(session_id)
            logging.info(f"Session summary (first 200 chars): {result[:200]}...")
            
            assert "explained_topics" in result, "explained_topics key not found in summary"
            assert "last_score" in result, "last_score key not found in summary"
            
            logging.info("test_populated_session_contains_keys passed")
            
        except AssertionError as e:
            logging.error(f"Session summary key validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_populated_session_contains_keys: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_result_is_markdown_formatted(self):
        """Session summary should be in markdown format."""
        logging.info("Starting test_result_is_markdown_formatted")
        
        try:
            session_id = "test-session"
            
            memory_set(session_id, "any_key", "any_value")
            logging.info(f"Stored test data in {session_id}")
            
            result = get_session_summary(session_id)
            
            contains_header = "# Session Memory:" in result
            logging.info(f"Contains markdown header: {contains_header}")
            
            assert "# Session Memory:" in result, f"Missing markdown header, got: {result[:100]}"
            
            logging.info("test_result_is_markdown_formatted passed - summary is markdown formatted")
            
        except AssertionError as e:
            logging.error(f"Markdown formatting validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_result_is_markdown_formatted: {str(e)}")
            raise LearningAcceleratorException(e, sys)