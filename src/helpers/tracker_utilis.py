import json, os
import streamlit as st


def delete_file_from_all_trackers(filepath: str, trackers: list[str]):
    """
    Remove a file entry from multiple tracker JSON files.
    """
    for tracker in trackers:
        if os.path.exists(tracker):
            with open(tracker, "r") as f:
                data = json.load(f)
            if filepath in data:
                del data[filepath]
                with open(tracker, "w") as f:
                    json.dump(data, f, indent=4)



def reload_page():

    # Inject JavaScript to refresh the browser
    st.markdown(
        """
        <script>
            window.location.reload();
        </script>
        """,
        unsafe_allow_html=True
    )
