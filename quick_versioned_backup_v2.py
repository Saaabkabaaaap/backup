import os
import shutil
import re
import subprocess

def get_versioned_filename(filepath):
    base, ext = os.path.splitext(filepath)
    dir_files = os.listdir(os.path.dirname(filepath) or ".")
    pattern = re.compile(re.escape(base) + r'_v(\d+)' + re.escape(ext))
    versions = [int(pattern.match(f).group(1)) for f in dir_files if pattern.match(f)]
    max_version = max(versions) if versions else 1
    new_version = max_version + 1
    return f"{base}_v{new_version}{ext}"

def backup_file(filepath):
    if not os.path.isfile(filepath):
        print(f"File {filepath} does not exist! Skipping.")
        return None
    new_file = get_versioned_filename(filepath)
    shutil.copy2(filepath, new_file)
    print(f"Backed up {filepath} as {new_file}")
    return new_file

def get_modified_files():
    try:
        # Get list of modified files tracked by git
        output = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
        files = []
        for line in output.splitlines():
            status = line[:2]
            file_path = line[3:]
            # Consider only modified or added files (you can customize)
            if status.strip() in ['M', 'A', 'AM', 'MM']:
                files.append(file_path)
        return files
    except subprocess.CalledProcessError as e:
        print("Error getting modified files:", e)
        return []

def run_git_commands(commit_message):
    try:
        subprocess.check_call(['git', 'add', '.'])
        subprocess.check_call(['git', 'commit', '-m', commit_message])
        subprocess.check_call(['git', 'push'])
        print("Changes committed and pushed successfully!")
    except subprocess.CalledProcessError as e:
        print("Git error:", e)

if __name__ == "__main__":
    modified_files = get_modified_files()
    if not modified_files:
        print("No modified files detected. Nothing to backup.")
    else:
        backed_up_files = []
        for f in modified_files:
            backed_file = backup_file(f)
            if backed_file:
                backed_up_files.append(backed_file)
        if backed_up_files:
            commit_msg = f"Versioned backup: {', '.join(backed_up_files)}"
            run_git_commands(commit_msg)
