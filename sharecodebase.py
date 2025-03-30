import os
import sys

# Define extensions
CODE_EXTENSIONS = {
    '.py', '.rs', '.js', '.ts', '.java', '.cpp', '.c', '.h',
    '.html', '.css', '.json', '.toml', '.yml', '.yaml', '.md',
}
SKIP_CONTENT_EXTENSIONS = {
    '.log', '.csv', '.tsv', '.db', '.sqlite', '.bin', '.exe',
    '.dll', '.so', '.zip', '.tar', '.gz', '.jpg', '.png', '.pdf',
    '.lock', 
}


# Folders to ignore completely
IGNORE_FOLDERS = {
    '.git', 'venv', '.venv', '__pycache__', 'node_modules', 'target',
    '.idea', '.vscode'
}

def is_text_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read(512)
        return True
    except:
        return False

def write_folder_tree(root_dir):
    tree_lines = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove unwanted folders from walking further
        dirnames[:] = [d for d in dirnames if d not in IGNORE_FOLDERS and not d.startswith('.')]
        rel_dir = os.path.relpath(dirpath, root_dir)
        indent_level = 0 if rel_dir == '.' else rel_dir.count(os.sep)
        indent = '    ' * indent_level
        tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")
        for f in sorted(filenames):
            if f.startswith('.'):
                continue
            sub_indent = '    ' * (indent_level + 1)
            tree_lines.append(f"{sub_indent}{f}")
    return "\n".join(tree_lines)

def collect_code_content(root_dir):
    contents = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_FOLDERS and not d.startswith('.')]
        for f in sorted(filenames):
            if f.startswith('.'):
                continue
            filepath = os.path.join(dirpath, f)
            relpath = os.path.relpath(filepath, root_dir)
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_CONTENT_EXTENSIONS:
                continue
            if ext in CODE_EXTENSIONS or is_text_file(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        code = file.read()
                    contents.append(f"\n\n# FILE: {relpath}\n\n```\n{code}\n```")
                except Exception as e:
                    contents.append(f"\n\n# FILE: {relpath}\n\n[Error reading file: {e}]")
    return "".join(contents)

def get_unique_filename(base_name="codebase_output.txt"):
    if not os.path.exists(base_name):
        return base_name

    base, ext = os.path.splitext(base_name)
    counter = 1
    while True:
        new_name = f"{base}_{counter}{ext}"
        if not os.path.exists(new_name):
            return new_name
        counter += 1


def main():
    if len(sys.argv) == 2:
        folder = sys.argv[1]
    else:
        print("👋 Hey! Please drag and drop your project folder here and press Enter:")
        folder = input("📁 Folder path: ").strip()

    if not os.path.isdir(folder):
        print("❌ Invalid folder path.")
        return

    output_file = get_unique_filename("codebase_output.txt")

    print("📂 Generating folder structure...")
    tree = write_folder_tree(folder)

    print("📄 Collecting code files...")
    code = collect_code_content(folder)

    print("📝 Writing output file...")
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# FOLDER STRUCTURE\n")
        out.write("```\n" + tree + "\n```\n")
        out.write("\n\n# CODE FILES\n")
        out.write(code)

    print(f"✅ Done. Output written to {output_file}")


if __name__ == "__main__":
    main()
