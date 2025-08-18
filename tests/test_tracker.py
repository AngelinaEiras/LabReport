import os
import json
import pytest
import pandas as pd
import streamlit as st
from datetime import datetime
from unittest import mock

# Import the classes from your src/models directory
from src.models.editorial import Editor
from src.models.experiment import Experiment, PLATE_ROW_RANGES
from src.models.report_creator import ExperimentReportManager

# --- Fixtures for common test setup ---

@pytest.fixture
def mock_editor_tracker_files(tmp_path):
    """
    Fixture to create temporary tracker files for the Editor class,
    and mock their paths.
    """
    editor_tracker_dir = tmp_path / "TRACKERS"
    editor_tracker_dir.mkdir()
    
    mock_file_tracker = editor_tracker_dir / "file_tracker.json"
    mock_editor_file_tracker = editor_tracker_dir / "editor_file_tracker.json"

    # Initialize empty JSON files
    mock_file_tracker.write_text(json.dumps({}))
    mock_editor_file_tracker.write_text(json.dumps({}))

    with mock.patch.object(Editor, 'TRACKER_FILE', str(mock_file_tracker)), \
         mock.patch.object(Editor, 'TRACKER_FILE_E', str(mock_editor_file_tracker)):
        yield str(mock_file_tracker), str(mock_editor_file_tracker)


@pytest.fixture
def mock_report_tracker_files(tmp_path):
    """
    Fixture to create temporary tracker files for the ReportManager class,
    and mock their paths.
    """
    report_tracker_dir = tmp_path / "TRACKERS"
    report_tracker_dir.mkdir(exist_ok=True) # Ensure it exists for report_creator
    
    mock_editor_file_tracker = report_tracker_dir / "editor_file_tracker.json"
    mock_report_metadata_file = report_tracker_dir / "report_metadata_tracker.json"

    # Initialize empty JSON files
    mock_editor_file_tracker.write_text(json.dumps({}))
    mock_report_metadata_file.write_text(json.dumps({}))

    with mock.patch.object(ExperimentReportManager, 'tracker_file', str(mock_editor_file_tracker)), \
         mock.patch.object(ExperimentReportManager, 'report_metadata_file', str(mock_report_metadata_file)):
        yield str(mock_editor_file_tracker), str(mock_report_metadata_file)


@pytest.fixture
def sample_excel_file(tmp_path):
    """
    Creates a dummy Excel file for testing Experiment class.
    """
    data = {
        'Well': ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3'],
        'Value': [10, 20, 30, 15, 25, 35, 12, 22, 32],
        'Other': ['X', 'Y', 'Z', 'A', 'B', 'C', 'D', 'E', 'F']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_experiment.xlsx"
    df.to_excel(file_path, index=False)
    return str(file_path)

@pytest.fixture
def sample_excel_file_96_wells(tmp_path):
    """
    Creates a dummy Excel file simulating a 96-well plate structure.
    """
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    cols = [str(i) for i in range(1, 13)] # 1 to 12
    
    data = []
    for r in rows:
        for c in cols:
            data.append({'Well': f'{r}{c}', 'Value': (ord(r) - ord('A') + 1) * int(c)})
    
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_96_well_experiment.xlsx"
    df.to_excel(file_path, index=False)
    return str(file_path)

@pytest.fixture
def sample_excel_file_12_wells(tmp_path):
    """
    Creates a dummy Excel file simulating a 12-well plate structure.
    """
    rows = ['A', 'B', 'C']
    cols = [str(i) for i in range(1, 5)] # 1 to 4
    
    data = []
    for r in rows:
        for c in cols:
            data.append({'Well': f'{r}{c}', 'Value': (ord(r) - ord('A') + 1) * int(c)})
    
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_12_well_experiment.xlsx"
    df.to_excel(file_path, index=False)
    return str(file_path)


# --- Tests for src.models.experiment.py (Experiment class) ---

def test_experiment_create_from_file(sample_excel_file):
    """Test Experiment creation from an Excel file."""
    exp = Experiment.create_experiment_from_file(sample_excel_file)
    assert isinstance(exp, Experiment)
    assert exp.name == "test_experiment"
    assert not exp.dataframe.empty
    assert exp.filepath == "experiments/test_experiment.json"
    assert isinstance(datetime.fromisoformat(exp.creation_date), datetime)


def test_experiment_save_and_load(tmp_path, sample_excel_file):
    """Test saving and loading an Experiment instance."""
    exp = Experiment.create_experiment_from_file(sample_excel_file)
    exp.filepath = str(tmp_path / "saved_experiment.json") # Set a temporary save path
    exp.save()

    loaded_exp = Experiment.load(exp.filepath)
    assert loaded_exp.name == exp.name
    pd.testing.assert_frame_equal(loaded_exp.dataframe, exp.dataframe)
    assert loaded_exp.creation_date == exp.creation_date
    assert loaded_exp.last_modified != exp.creation_date # last_modified should be updated on save


def test_experiment_split_into_subdatasets_96_wells(sample_excel_file_96_wells):
    """Test splitting a 96-well plate into subdatasets."""
    exp = Experiment.create_experiment_from_file(sample_excel_file_96_wells)
    subdatasets, valid_rows = Experiment.split_into_subdatasets(exp.dataframe)
    
    assert len(subdatasets) > 0 # Expect at least one subdataset
    assert valid_rows == PLATE_ROW_RANGES["96 wells"]
    
    # Check that each subdataset is a DataFrame
    for sub_df in subdatasets:
        assert isinstance(sub_df, pd.DataFrame)
        assert 'Well' in sub_df.columns # Ensure columns are preserved


def test_experiment_split_into_subdatasets_12_wells(sample_excel_file_12_wells):
    """Test splitting a 12-well plate into subdatasets."""
    exp = Experiment.create_experiment_from_file(sample_excel_file_12_wells)
    subdatasets, valid_rows = Experiment.split_into_subdatasets(exp.dataframe)
    
    assert len(subdatasets) > 0 # Expect at least one subdataset
    assert valid_rows == PLATE_ROW_RANGES["12 wells"]
    
    # Check that each subdataset is a DataFrame
    for sub_df in subdatasets:
        assert isinstance(sub_df, pd.DataFrame)
        assert 'Well' in sub_df.columns # Ensure columns are preserved


def test_experiment_split_into_subdatasets_empty_df():
    """Test splitting an empty DataFrame."""
    empty_df = pd.DataFrame(columns=['Well', 'Value'])
    subdatasets, valid_rows = Experiment.split_into_subdatasets(empty_df)
    assert len(subdatasets) == 0
    assert valid_rows == PLATE_ROW_RANGES["96 wells"] # Default if no rows found


# --- Tests for src.models.editorial.py (Editor class) ---

# Mock streamlit functions that interact with UI directly
@mock.patch('streamlit.selectbox')
@mock.patch('streamlit.button')
@mock.patch('streamlit.text_input')
@mock.patch('streamlit.dataframe')
@mock.patch('streamlit.expander')
@mock.patch('streamlit.write')
@mock.patch('streamlit.warning')
@mock.patch('streamlit.info')
@mock.patch('streamlit.success')
@mock.patch('streamlit.markdown')
@mock.patch('streamlit.columns')
@mock.patch('streamlit.rerun')
@mock.patch('st_table_select_cell.st_table_select_cell') # Mock the custom component
def test_editor_initialization_and_tracker_load(
    mock_st_table_select_cell, mock_rerun, mock_columns, mock_markdown, mock_success, 
    mock_info, mock_warning, mock_write, mock_expander, mock_dataframe, 
    mock_text_input, mock_button, mock_selectbox, 
    mock_editor_tracker_files, tmp_path
):
    """Test Editor class initialization and tracker loading."""
    mock_file_tracker_path, mock_editor_file_tracker_path = mock_editor_tracker_files

    # Populate mock_file_tracker with some dummy experiment data
    dummy_exp_path = str(tmp_path / "dummy_exp.xlsx")
    with open(mock_file_tracker_path, 'w') as f:
        json.dump({dummy_exp_path: {"is_experiment": True, "metadata": {}}}, f)
    
    # Mock st.session_state for initialization
    with mock.patch('streamlit.session_state', new={}):
        editor = Editor()

        assert editor.experiments_list == [dummy_exp_path]
        assert st.session_state.experiments_list == [dummy_exp_path]
        assert st.session_state.selected_experiment_key_in_session is None
        assert st.session_state.selected_subdataset_index == 0
        assert st.session_state.current_group == []


@mock.patch('streamlit.selectbox')
@mock.patch('streamlit.button')
@mock.patch('streamlit.text_input')
@mock.patch('streamlit.dataframe')
@mock.patch('streamlit.expander')
@mock.patch('streamlit.write')
@mock.patch('streamlit.warning')
@mock.patch('streamlit.info')
@mock.patch('streamlit.success')
@mock.patch('streamlit.markdown')
@mock.patch('streamlit.columns')
@mock.patch('streamlit.rerun')
@mock.patch('st_table_select_cell.st_table_select_cell')
@mock.patch('src.models.experiment.Experiment.create_experiment_from_file')
@mock.patch('src.models.experiment.Experiment.split_into_subdatasets')
def test_editor_handle_experiment(
    mock_split_subdatasets, mock_create_experiment, mock_st_table_select_cell, mock_rerun, 
    mock_columns, mock_markdown, mock_success, mock_info, mock_warning, mock_write, 
    mock_expander, mock_dataframe, mock_text_input, mock_button, mock_selectbox, 
    mock_editor_tracker_files, tmp_path
):
    """Test Editor's _handle_experiment method."""
    mock_file_tracker_path, mock_editor_file_tracker_path = mock_editor_tracker_files

    # Setup mock Experiment instance
    mock_exp_instance = mock.Mock()
    mock_exp_instance.dataframe = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    mock_create_experiment.return_value = mock_exp_instance

    # Setup mock split_into_subdatasets return value
    mock_split_subdatasets.return_value = ([pd.DataFrame({'X': [10]})], ["A", "B"])

    editor = Editor()
    test_exp_path = str(tmp_path / "test_exp.xlsx")

    # Mock st.session_state for the method call
    with mock.patch('streamlit.session_state', new={
        "selected_experiment_for_subdatasets": None,
        "subdatasets": [],
        "selected_subdataset_index": 0
    }):
        editor.file_data = {} # Ensure file_data is clean for this test

        mock_create_experiment.assert_called_once_with(test_exp_path)
        mock_write.assert_any_call("## Original Dataset")
        mock_dataframe.assert_called_once_with(mock_exp_instance.dataframe)
        mock_split_subdatasets.assert_called_once_with(mock_exp_instance.dataframe)
        
        assert st.session_state.selected_experiment_for_subdatasets == test_exp_path
        assert len(st.session_state.subdatasets) == 1
        assert st.session_state.selected_subdataset_index == 0
        assert editor.file_data[test_exp_path]["plate_type"] == "24 wells" # Based on ["A", "B"] valid rows

# --- Tests for src.models.report_creator.py (ExperimentReportManager class) ---

def test_report_manager_initialization(mock_report_tracker_files):
    """Test ExperimentReportManager initialization and tracker loading."""
    mock_editor_file_tracker_path, mock_report_metadata_file_path = mock_report_tracker_files

    manager = ExperimentReportManager()
    assert manager.editor_data == {}
    assert manager.report_data == {}
    assert manager.tracker_file == mock_editor_file_tracker_path
    assert manager.report_metadata_file == mock_report_metadata_file_path


def test_report_manager_save_and_load_report_data(mock_report_tracker_files):
    """Test saving and loading report metadata."""
    mock_editor_file_tracker_path, mock_report_metadata_file_path = mock_report_tracker_files

    manager = ExperimentReportManager()
    
    test_report_data = {
        "experiment_metadata": {
            "exp1": {"Plate Type": "96 wells", "Custom Field": "Value"}
        },
        "subdataset_metadata": {
            "exp1_0": {"Sub Custom": "Sub Value"}
        }
    }
    manager.report_data = test_report_data
    manager.save_json_file(manager.report_data)

    # Create a new manager to simulate loading from disk
    new_manager = ExperimentReportManager()
    new_manager.load_data() # Explicitly call load_data
    
    assert new_manager.report_data == test_report_data


@mock.patch('streamlit.expander')
@mock.patch('streamlit.dataframe')
def test_report_manager_show_dataframe(mock_dataframe, mock_expander):
    """Test show_dataframe method."""
    mock_expander.return_value.__enter__.return_value = None # Mock the context manager
    manager = ExperimentReportManager()
    test_data = [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]
    
    returned_df = manager.show_dataframe("Test Title", test_data)
    
    mock_expander.assert_called_once_with("📊 Test Title", expanded=False)
    mock_dataframe.assert_called_once()
    assert not returned_df.empty
    assert returned_df.shape == (2, 2)


@mock.patch('streamlit.text_input')
@mock.patch('streamlit.selectbox')
@mock.patch('streamlit.date_input')
@mock.patch('streamlit.warning')
@mock.patch('streamlit.info')
@mock.patch('streamlit.success')
@mock.patch('streamlit.markdown')
@mock.patch('streamlit.columns')
@mock.patch('streamlit.rerun')
def test_report_manager_display_metadata_fields(
    mock_rerun, mock_columns, mock_markdown, mock_success, mock_info, mock_warning,
    mock_date_input, mock_selectbox, mock_text_input
):
    """Test display_metadata_fields method."""
    manager = ExperimentReportManager()
    metadata_definitions = {
        "Field1": {"type": "text_input", "default_source": "Default1"},
        "Field2": {"type": "selectbox", "options": ["OptA", "OptB"], "default_source": "OptA"},
        "Field3": {"type": "date_input", "default_source": "2023-01-01"}
    }
    current_metadata = {}

    mock_text_input.return_value = "NewValue1"
    mock_selectbox.return_value = "OptB"
    mock_date_input.return_value = datetime(2023, 2, 1).date()

    changed = manager.display_metadata_fields(metadata_definitions, current_metadata)

    assert changed is True
    assert current_metadata["Field1"] == "NewValue1"
    assert current_metadata["Field2"] == "OptB"
    assert current_metadata["Field3"] == "2023-02-01" # Stored as string


@mock.patch('streamlit.text_input')
@mock.patch('streamlit.button')
@mock.patch('streamlit.write')
@mock.patch('streamlit.warning')
@mock.patch('streamlit.info')
@mock.patch('streamlit.success')
@mock.patch('streamlit.markdown')
@mock.patch('streamlit.columns')
@mock.patch('streamlit.rerun')
def test_report_manager_display_custom_metadata(
    mock_rerun, mock_columns, mock_markdown, mock_success, mock_info, mock_warning, 
    mock_write, mock_button, mock_text_input,
    mock_report_tracker_files
):
    """Test display_custom_metadata method (editing and deleting)."""
    mock_columns.return_value = [mock.Mock(), mock.Mock(), mock.Mock()] # Mock columns for layout
    manager = ExperimentReportManager()
    manager.report_data = {"subdataset_metadata": {"exp1_0": {"Custom1": "Value1", "Custom2": "Value2"}}}
    current_metadata = manager.report_data["subdataset_metadata"]["exp1_0"]
    predefined_fields = {}
    unique_key_prefix = "exp1_0"

    # Test editing a custom field
    mock_text_input.side_effect = ["NewValue1"] # For Custom1
    mock_button.side_effect = [False] # No delete button clicked initially

    changed = manager.display_custom_metadata(current_metadata, predefined_fields, unique_key_prefix)
    assert changed is True
    assert current_metadata["Custom1"] == "NewValue1"
    assert current_metadata["Custom2"] == "Value2" # Unchanged

    # Test deleting a custom field
    mock_text_input.side_effect = ["Value1", "Value2"] # Keep values same
    mock_button.side_effect = [False, True] # Click delete for Custom2

    changed = manager.display_custom_metadata(current_metadata, predefined_fields, unique_key_prefix)
    assert changed is True
    assert "Custom2" not in current_metadata
    mock_rerun.assert_called_once() # Rerun should be called on deletion


@mock.patch('streamlit.form')
@mock.patch('streamlit.text_input')
@mock.patch('streamlit.form_submit_button')
@mock.patch('streamlit.warning')
@mock.patch('streamlit.success')
@mock.patch('streamlit.rerun')
def test_report_manager_add_custom_metadata_field(
    mock_rerun, mock_success, mock_warning, mock_form_submit_button, mock_text_input,
    mock_form, mock_report_tracker_files
):
    """Test add_custom_metadata_field method."""
    # Mock the form context manager
    mock_form.return_value.__enter__.return_value = mock.Mock()
    
    manager = ExperimentReportManager()
    manager.report_data = {"subdataset_metadata": {"exp1_0": {}}}
    current_metadata = manager.report_data["subdataset_metadata"]["exp1_0"]
    unique_key_prefix = "exp1_0"

    # Simulate adding a new field
    mock_text_input.side_effect = ["NewField", "FieldValue"]
    mock_form_submit_button.return_value = True # Form submitted

    manager.add_custom_metadata_field(current_metadata, unique_key_prefix)

    assert "NewField" in current_metadata
    assert current_metadata["NewField"] == "FieldValue"
    mock_success.assert_called_once_with("Added custom field: `NewField`")
    mock_rerun.assert_called_once()

    # Simulate adding a duplicate field
    mock_text_input.side_effect = ["NewField", "AnotherValue"] # Same name
    mock_form_submit_button.return_value = True

    mock_success.reset_mock() # Reset mock to check for new calls
    mock_rerun.reset_mock()

    manager.add_custom_metadata_field(current_metadata, unique_key_prefix)
    mock_warning.assert_called_once_with("Field 'NewField' already exists.")
    mock_success.assert_not_called()
    mock_rerun.assert_not_called()


@mock.patch('weasyprint.HTML')
@mock.patch('os.makedirs')
@mock.patch('builtins.open', new_callable=mock.mock_open) # Mock file open for PDF write
def test_report_manager_generate_pdf_report(
    mock_open, mock_makedirs, mock_weasyprint_html,
    mock_report_tracker_files, tmp_path
):
    """Test generate_pdf_report method."""
    # Mock HTML().write_pdf()
    mock_weasyprint_html.return_value.write_pdf.return_value = None

    manager = ExperimentReportManager()
    manager.report_data = {"experiment_metadata": {"exp_test": {"GeneralField": "GeneralValue"}}}
    
    general_exp_meta = manager.report_data["experiment_metadata"]["exp_test"]

    all_subdatasets_data = [
        {
            "sub_custom_metadata": {"SubCustom1": "SubValue1", "Notes": "Some notes here."},
            "original_df": pd.DataFrame({"A": [1, 2]}),
            "modified_df": pd.DataFrame({"A": [10, 20]}),
            "cell_groups": {"Group1": {"cells": [], "stats": {}}},
            "notes": "Some notes here." # This is now passed from sub_custom_metadata.get("Notes")
        },
        {
            "sub_custom_metadata": {"SubCustom2": "SubValue2"},
            "original_df": pd.DataFrame({"B": [3, 4]}),
            "modified_df": pd.DataFrame({"B": [30, 40]}),
            "cell_groups": {},
            "notes": ""
        }
    ]

    # Mock st.session_state for the selected experiment key
    with mock.patch('streamlit.session_state', new={"selected_experiment_key_for_report": "exp_test"}):
        pdf_path = manager.generate_pdf_report(general_exp_meta, all_subdatasets_data)

        # Assertions
        mock_weasyprint_html.assert_called_once()
        html_string_arg = mock_weasyprint_html.call_args[0][0]
        assert "<h1>Experiment Report</h1>" in html_string_arg
        assert "<h2>General Experiment Metadata</h2>" in html_string_arg
        assert "GeneralField" in html_string_arg
        assert "GeneralValue" in html_string_arg
        assert "<h2>Sub-dataset 1</h2>" in html_string_arg
        assert "<h3>Sub-dataset Specific Metadata</h3>" in html_string_arg
        assert "SubCustom1" in html_string_arg
        assert "SubValue1" in html_string_arg
        assert "<h3>Notes:</h3><p>Some notes here.</p>" in html_string_arg
        assert "<h2>Sub-dataset 2</h2>" in html_string_arg
        assert "SubCustom2" in html_string_arg
        assert "SubValue2" in html_string_arg
        assert "<h3>Original Subdataset</h3>" in html_string_arg
        assert "<h3>Modified Subdataset</h3>" in html_string_arg
        assert "<h4>Group: Group1</h4>" in html_string_arg # Check for h4
        assert mock_weasyprint_html.return_value.write_pdf.called
        assert pdf_path == "/tmp/report.pdf" # Default path

