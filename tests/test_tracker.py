import os
import json
import tempfile
import pytest
from datetime import datetime
from unittest import mock

# Adjust imports based on your project structure
# Assuming get_file_metadata, save_tracker, and file_data are in src/file_manager/file_manager.py
# If they are in pages/Editor.py, this would be a different (and less ideal for testing) import.
from src.models import ( # Adjust this import path as necessary
    editorial,
    experiment,
    file_selector as global_file_data, # Import the global file_data to patch it
    report_creator # Assuming is_experiment is also here
)


# ############################# criar para cada class/pag?????


# # Assuming Experiment class is in src/models/experiment.py
# from src.models.experiment import Experiment

# # Test for get_file_metadata
# def test_get_file_metadata_creates_expected_keys(tmp_path):
#     """
#     Tests that get_file_metadata correctly extracts file metadata
#     and that the returned dictionary contains the expected keys
#     with appropriate data types.
#     """
#     test_file = tmp_path / "20230308_PB triton seed 06.03.xlsx"
#     test_file.write_text("Hello, test!")

#     metadata = get_file_metadata(str(test_file))

#     assert "size_kb" in metadata
#     assert "created" in metadata
#     assert "last_modified" in metadata
#     assert isinstance(metadata["size_kb"], float)
#     # Check if the 'created' timestamp is a parsable ISO format string
#     assert datetime.fromisoformat(metadata["created"])
#     # Check if the 'last_modified' timestamp is a parsable ISO format string
#     assert datetime.fromisoformat(metadata["last_modified"])


# # Test for save_tracker
# def test_save_tracker_creates_valid_json(tmp_path):
#     """
#     Tests that save_tracker correctly saves the file_data to a JSON file.
#     It mocks the global TRACKER_FILE path and file_data dictionary
#     within the module where they are used by save_tracker.
#     """
#     fake_data = {
#         "file.txt": {
#             "metadata": {
#                 "size_kb": 1.23,
#                 "created": datetime.now().isoformat(),
#                 "last_modified": datetime.now().isoformat(),
#             },
#             "note": "example note",
#             "is_experiment": False,
#         }
#     }

#     tracker_file = tmp_path / "file_tracker.json"

#     # Patch the module-level TRACKER_FILE and file_data from src.file_manager.file_manager
#     # The path to patch is where these variables are imported or defined in the module
#     # that `save_tracker` uses them.
#     with mock.patch("src.file_manager.file_manager.TRACKER_FILE", str(tracker_file)), \
#          mock.patch("src.file_manager.file_manager.file_data", fake_data): # Patch the global file_data
#         save_tracker()

#     assert tracker_file.exists()
#     with open(tracker_file) as f:
#         content = json.load(f)
#         assert "file.txt" in content
#         assert content["file.txt"]["note"] == "example note"


# # Test for is_experiment - valid case
# # Patch the Experiment class where it is used within the is_experiment function.
# # Assuming is_experiment is in src.file_manager.file_manager and it imports Experiment from src.models.experiment
# @mock.patch("src.file_manager.file_manager.Experiment") # Adjust this patch path if Experiment is imported differently within file_manager.py
# def test_is_experiment_valid(mock_experiment_class, tmp_path):
#     """
#     Tests the is_experiment function when a valid experiment file is provided.
#     It mocks the Experiment class and its methods to simulate expected behavior.
#     """
#     # Simulate .xlsx file
#     fake_file = tmp_path / "test.xlsx"
#     fake_file.write_text("placeholder") # Content doesn't matter for mock

#     # Mock return values from Experiment.create_experiment_from_file
#     mock_exp_instance = mock.Mock()
#     mock_exp_instance.dataframe.empty = False
#     mock_exp_instance.dataframe.shape = (10, 5) # Non-empty shape
    
#     # Mock the return value of the class method create_experiment_from_file
#     mock_experiment_class.create_experiment_from_file.return_value = mock_exp_instance
    
#     # Mock the static method split_into_subdatasets on the mocked Experiment class
#     mock_experiment_class.split_into_subdatasets.return_value = ([mock.Mock()], ["A", "B"]) # Simulate subdatasets found, returning a list of mock DFs and valid rows

#     assert is_experiment(str(fake_file)) is True


# # Test for is_experiment - invalid due to empty dataframe
# @mock.patch("src.file_manager.file_manager.Experiment") # Adjust this patch path
# def test_is_experiment_invalid_due_to_empty_df(mock_experiment_class, tmp_path):
#     """
#     Tests the is_experiment function when the mocked Experiment
#     returns an empty dataframe, indicating it's not a valid experiment.
#     """
#     fake_file = tmp_path / "test.xlsx"
#     fake_file.write_text("placeholder")

#     # Mock empty dataframe
#     mock_exp_instance = mock.Mock()
#     mock_exp_instance.dataframe.empty = True # Simulate empty dataframe
#     mock_exp_instance.dataframe.shape = (0, 0) # Empty shape
    
#     mock_experiment_class.create_experiment_from_file.return_value = mock_exp_instance
#     # No need to mock split_into_subdatasets if create_experiment_from_file already returns an empty df
#     # as is_experiment should check for empty df first.

#     assert is_experiment(str(fake_file)) is False

# # Test for is_experiment - invalid due to no subdatasets (after successful df load)
# @mock.patch("src.file_manager.file_manager.Experiment") # Adjust this patch path
# def test_is_experiment_invalid_due_to_no_subdatasets(mock_experiment_class, tmp_path):
#     """
#     Tests the is_experiment function when Experiment.split_into_subdatasets
#     returns an empty list of subdatasets.
#     """
#     fake_file = tmp_path / "test.xlsx"
#     fake_file.write_text("placeholder")

#     mock_exp_instance = mock.Mock()
#     mock_exp_instance.dataframe.empty = False
#     mock_exp_instance.dataframe.shape = (10, 5)

#     mock_experiment_class.create_experiment_from_file.return_value = mock_exp_instance
#     mock_experiment_class.split_into_subdatasets.return_value = ([], []) # Simulate no subdatasets found

#     assert is_experiment(str(fake_file)) is False

