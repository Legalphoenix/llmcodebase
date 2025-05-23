Codebase Snapshotter: https://www.loom.com/share/210b5cf9c681466eb534dcf8a084a321?sid=972862d4-c2a8-47b7-9c71-aa2c8fcca06e

Creates a single .txt snapshot (folder structure & code content) of a project. Live monitors and auto-updates the snapshot. Ideal for LLMs or code sharing.

Quick Start

Prerequisites:
1. Save the code from sharecodebase.py
2. Create a venv and pip install watchdog

Run Script in your terminal:
1. Python sharecodebase.py
2. Then drag your project folder to the terminal and press Enter.


Output:
A file named <project_folder_name>_codebase.txt will be created in the script's current working directory.
Format: Folder tree followed by code content marked with FILE: path/to/file.
EXAMPLE: https://docs.google.com/document/d/1UcmkZuv-OIEzeIsgBeT22ytkv-rJS_teSjUP7xmz-LM/edit?usp=sharing

Monitoring:
The script monitors the folder for changes (i.e: when you change a file and save it) and regenerates the snapshot.
Press Ctrl+C to stop.

Configuration

Customize behavior by editing these sets at the top of the script:
CODE_EXTENSIONS: File types to include content from.
SKIP_CONTENT_EXTENSIONS: File types to list in tree but skip content.
IGNORE_FOLDERS: Folders to completely exclude.

Tip: if you struggle to follow what to do, use ChatGPT to tell you what to do.
