# LabReport

LabReport is a local Streamlit app for tracking files, editing experiment data, and generating reports.

## Requirements

- Python 3.10 or later
- Tkinter, which provides the file-picker dialog. On Ubuntu/Debian, install it if needed with `sudo apt install python3-tk`.

## First-time setup

Clone the repository, or download and extract it. If cloning:

```bash
git clone https://github.com/AngelinaEiras/LabReport.git
cd LabReport
```

Open a terminal in the project folder—the folder containing `Explorer.py`, `requirements.txt`, `images/`, `pages/`, and `src/`. If you already downloaded the project, do not clone it again.

### Linux

Run these commands from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p TRACKERS
```

## Start the app

After setup, open a terminal and run these commands. Replace `/path/to/LabReport` with the full path to the folder where you cloned or extracted the project:

```bash
cd /path/to/LabReport
.venv/bin/python -m streamlit run Explorer.py --server.headless true
```

For example, if the project is in `~/Documents/LabReport`, use `cd ~/Documents/LabReport`. Run the app from the project folder so it can find `images/`, `pages/`, and its other files. Keep `.venv/bin/python`, `Explorer.py`, and the Streamlit options unchanged unless you chose a different virtual-environment folder name. The headless option keeps Streamlit from opening a browser automatically; open the local address it prints instead.

## What stays the same, and what to change

- Always run the commands from the project folder. This is needed so the app can find `images/`, `pages/`, and its other files.
- Keep `Explorer.py` as the Streamlit entry point and `requirements.txt` as the dependency file.
- Replace `/path/to/LabReport` with the location of your own project folder; it will be different on each computer.
- Use the command block for your operating system. If you rename `.venv`, use that same new name in both the create and activate commands.
- `TRACKERS/` is where LabReport saves its local tracking data. It is created during setup and is not shared automatically with other computers.

## Using the app

Streamlit prints a local address, usually `http://localhost:8501`, when it starts. Open that address in your browser. Select **Add new file** to choose a file, then use the sidebar to open the Editor and Report pages. The app uses files accessible on the computer where it is running; after moving to another computer, add those files again. Press `Ctrl+C` in the terminal to stop the app.
