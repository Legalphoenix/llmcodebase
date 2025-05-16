import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import functools
import re # For sanitizing filename

# Define extensions
# Define extensions
CODE_EXTENSIONS = {
    '.py', '.rs', '.js', '.ts', '.java', '.cpp', '.c', '.h',
    '.html', '.css', '.json', '.toml', '.yml', '.jsx', '.yaml', '.md',
    '.php', '.rb', '.go', '.swift', '.kt', '.cs', '.scala', '.sh',
    '.sql', '.r', '.dart', '.jl', '.lua', '.groovy', '.ps1',
    '.xml', '.properties', '.ini', '.rst',
}
SKIP_CONTENT_EXTENSIONS = {
    '.log', '.csv', '.tsv', '.db', '.sqlite', '.bin', '.exe',
    '.dll', '.so', '.zip', '.tar', '.gz', '.jpg', '.png', '.pdf',
    '.lock', '.iso', '.img', '.dat', '.env', '.gitignore', '.editorconfig', '.gitattributes', '.dockerignore',
    '.npmignore', '.htaccess',
}

# Folders to ignore completely
IGNORE_FOLDERS = {
    '.git', 'venv', '.venv', '__pycache__', 'node_modules', 'target',
    '.idea', '.vscode', 'dist', 'build', 'out', 'vendor', 'bundle', 'logs', 'temp', 'tmp',
    '.cache', '.gradle', '.mvn', 'bower_components', 'report', 'test-results',
    'coverage',
}

# Removed DEFAULT_OUTPUT_FILENAME

def sanitize_filename(name):
    """
    Sanitizes a string to be used as a part of a filename.
    Replaces spaces with underscores and removes characters not allowed in filenames.
    """
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w\-. ]', '', name) # Keep word chars, hyphens, periods, underscores
    if not name: # If sanitization results in an empty string
        name = "unnamed_folder"
    return name

def is_text_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read(512) # Try to read a small chunk
        return True
    except UnicodeDecodeError: # It's binary or wrong encoding
        return False
    except Exception: # Other errors, assume not text or not readable
        return False

def write_folder_tree(root_dir, ignored_folders_set):
    tree_lines = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in ignored_folders_set and not d.startswith('.')]
        
        rel_dir = os.path.relpath(dirpath, root_dir)
        indent_level = 0 if rel_dir == '.' else rel_dir.count(os.sep) + 1
        
        if rel_dir == '.':
            tree_lines.append(f"{os.path.basename(root_dir)}/")
        else:
            indent = '    ' * (indent_level -1)
            tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")

        sub_indent = '    ' * indent_level
        for f in sorted(filenames):
            if f.startswith('.'):
                continue
            tree_lines.append(f"{sub_indent}{f}")
            
    return "\n".join(tree_lines)

def collect_code_content(root_dir, ignored_folders_set, code_extensions_set, skip_content_extensions_set):
    contents = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in ignored_folders_set and not d.startswith('.')]
        
        for f in sorted(filenames):
            if f.startswith('.'):
                continue
            
            filepath = os.path.join(dirpath, f)
            relpath = os.path.relpath(filepath, root_dir)
            ext = os.path.splitext(f)[1].lower()

            if ext in skip_content_extensions_set:
                continue
            
            if ext in code_extensions_set or is_text_file(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        code = file.read()
                    contents.append(f"\n\n# FILE: {relpath}\n\n```\n{code}\n```")
                except Exception as e:
                    contents.append(f"\n\n# FILE: {relpath}\n\n[Error reading file: {e}]")
    return "".join(contents)

def generate_codebase_snapshot(target_folder_abs, output_filepath_abs, 
                               ignored_folders_set, code_extensions_set, 
                               skip_extensions_set):
    print(f"🔄 Generating codebase snapshot for '{target_folder_abs}'...")
    
    print(" L 📂 Generating folder structure...")
    tree = write_folder_tree(target_folder_abs, ignored_folders_set)

    print(" L 📄 Collecting code files...")
    code = collect_code_content(target_folder_abs, ignored_folders_set, 
                                code_extensions_set, skip_extensions_set)

    print(f" L 📝 Writing output to {output_filepath_abs}...")
    try:
        with open(output_filepath_abs, 'w', encoding='utf-8') as out:
            out.write("# FOLDER STRUCTURE\n")
            out.write("```\n" + tree + "\n```\n")
            out.write("\n\n# CODE FILES\n")
            out.write(code)
        print(f"✅ Snapshot updated: {output_filepath_abs}")
    except Exception as e:
        print(f"❌ Error writing output file: {e}")


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, folder_to_monitor_abs, output_filepath_abs, 
                 ignored_folders_set, regeneration_callback):
        super().__init__()
        self.folder_to_monitor_abs = folder_to_monitor_abs
        self.output_filepath_abs = os.path.abspath(output_filepath_abs)
        self.ignored_folders_set = ignored_folders_set
        self.regeneration_callback = regeneration_callback
        self.last_processed_time = 0.0
        self.debounce_period = 2.0

    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_processed_time < self.debounce_period:
            return

        event_path = os.path.abspath(event.src_path)

        if event_path == self.output_filepath_abs:
            return

        try:
            relative_event_path = os.path.relpath(event_path, self.folder_to_monitor_abs)
        except ValueError: 
            if not event_path.startswith(self.folder_to_monitor_abs):
                return

        path_components = relative_event_path.split(os.sep)
        
        for component in path_components:
            if component in self.ignored_folders_set:
                return
            if component.startswith('.') and component not in ['.', '..']:
                return
        
        basename = os.path.basename(event_path)
        if basename.startswith('.') and basename not in ['.', '..'] and basename not in self.ignored_folders_set:
            return

        print(f"ℹ️ Change detected: {event.event_type} on {event.src_path}.")
        self.last_processed_time = current_time
        self.regeneration_callback()


def main():
    if len(sys.argv) == 2:
        folder_input = sys.argv[1]
    else:
        print("👋 Hey! Please drag and drop your project folder here and press Enter:")
        folder_input = input("📁 Folder path: ").strip().replace("'", "")

    if not os.path.isdir(folder_input):
        print(f"❌ Invalid folder path: {folder_input}")
        return

    folder_abs = os.path.abspath(folder_input)
    
    # Generate output filename based on the input folder name
    folder_basename = os.path.basename(folder_abs)
    sanitized_folder_name = sanitize_filename(folder_basename)
    output_filename = f"{sanitized_folder_name}_codebase.txt"
    
    # Output file will be in the current working directory of the script
    output_filepath_abs = os.path.abspath(output_filename)

    print(f"Monitored folder: {folder_abs}")
    print(f"Output file:      {output_filepath_abs}")


    regeneration_function_partial = functools.partial(
        generate_codebase_snapshot,
        folder_abs,
        output_filepath_abs,
        IGNORE_FOLDERS, 
        CODE_EXTENSIONS,
        SKIP_CONTENT_EXTENSIONS
    )

    regeneration_function_partial()

    event_handler = ChangeHandler(
        folder_abs,
        output_filepath_abs,
        IGNORE_FOLDERS,
        regeneration_function_partial
    )
    observer = Observer()
    observer.schedule(event_handler, folder_abs, recursive=True)
    observer.start()

    print(f"👀 Monitoring folder '{folder_abs}' for changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user.")
    finally:
        observer.stop()
        observer.join()
        print("👋 Exiting.")

if __name__ == "__main__":
    main()