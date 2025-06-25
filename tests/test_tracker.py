import os
import json
import tempfile
import pytest
from datetime import datetime
from unittest import mock

# Ensure these imports match your actual LabReport.py structure
from LabReport.Lab_Report import (
    get_file_metadata,
    save_tracker,
    is_experiment,
)

# Test for get_file_metadata
def test_get_file_metadata_creates_expected_keys(tmp_path):
    """
    Tests that get_file_metadata correctly extracts file metadata
    and that the returned dictionary contains the expected keys
    with appropriate data types.
    """
    test_file = tmp_path / "example.txt"
    test_file.write_text("Hello, test!")

    metadata = get_file_metadata(str(test_file))

    assert "size_kb" in metadata
    assert "created" in metadata
    assert "last_modified" in metadata
    assert isinstance(metadata["size_kb"], float)
    # Check if the 'created' timestamp is a parsable ISO format string
    assert datetime.fromisoformat(metadata["created"])


# Test for save_tracker
def test_save_tracker_creates_valid_json(tmp_path):
    """
    Tests that save_tracker correctly saves the file_data to a JSON file.
    It mocks the global TRACKER_FILE path and file_data dictionary
    within the Lab_Report module to control the test environment.
    """
    fake_data = {
        "file.txt": {
            "metadata": {
                "size_kb": 1.23,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
            },
            "note": "example note",
            "is_experiment": False,
        }
    }

    tracker_file = tmp_path / "file_tracker.json"

    # Patch the module-level TRACKER_FILE and file_data from LabReport.Lab_Report
    # The path to patch is where these variables are imported or defined in the module
    # that `save_tracker` uses them.
    with mock.patch("LabReport.Lab_Report.TRACKER_FILE", str(tracker_file)), \
         mock.patch("LabReport.Lab_Report.file_data", fake_data):
        save_tracker()

    assert tracker_file.exists()
    with open(tracker_file) as f:
        content = json.load(f)
        assert "file.txt" in content
        assert content["file.txt"]["note"] == "example note"


# Test for is_experiment - valid case
# Assuming 'Experiment' class is imported into LabReport.Lab_Report from
# LabReport.src.models.excel_manager (common pattern for your structure).
# You MUST verify the exact import path within LabReport/Lab_Report.py
# For example, if Lab_Report.py has: `from LabReport.src.models.excel_manager import Experiment`
# Then the patch path is 'LabReport.Lab_Report.Experiment'
@mock.patch("LabReport.Lab_Report.Experiment")
def test_is_experiment_valid(mock_experiment, tmp_path):
    """
    Tests the is_experiment function when a valid experiment file is provided.
    It mocks the Experiment class and its methods to simulate expected behavior.
    """
    # Simulate .xlsx file
    fake_file = tmp_path / "test.xlsx"
    fake_file.write_text("placeholder") # Content doesn't matter for mock

    # Mock return values from Experiment.create_experiment_from_file
    mock_exp_instance = mock.Mock()
    mock_exp_instance.dataframe.empty = False
    mock_exp_instance.dataframe.shape = (10, 5) # Non-empty shape
    # Mock the static method or class method used directly
    mock_experiment.create_experiment_from_file.return_value = mock_exp_instance
    mock_experiment.split_into_subdatasets.return_value = [1, 2, 3] # Simulate subdatasets found

    assert is_experiment(str(fake_file)) is True


# Test for is_experiment - invalid due to empty dataframe
@mock.patch("LabReport.Lab_Report.Experiment")
def test_is_experiment_invalid_due_to_empty_df(mock_experiment, tmp_path):
    """
    Tests the is_experiment function when the mocked Experiment
    returns an empty dataframe, indicating it's not a valid experiment.
    """
    fake_file = tmp_path / "test.xlsx"
    fake_file.write_text("placeholder")

    # Mock empty dataframe
    mock_exp_instance = mock.Mock()
    mock_exp_instance.dataframe.empty = True # Simulate empty dataframe
    mock_exp_instance.dataframe.shape = (0, 0) # Empty shape
    mock_experiment.create_experiment_from_file.return_value = mock_exp_instance

    assert is_experiment(str(fake_file)) is False
