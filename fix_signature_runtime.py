# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This script safely replaces global print()
# with controlled __main__ guarded print
# =========================================

import os

# 🔹 Target line inserted earlier
TARGET_LINE = 'print("HiddenEdge Engine v1.0 | SB3PM")'

# 🔹 Safe replacement
REPLACEMENT_LINES = [
    'if __name__ == "__main__":\n',
    '    print("HiddenEdge Engine v1.0 | SB3PM")\n'
]

# 🔹 Folders to ignore
EXCLUDE_DIRS = {"venv", "__pycache__", ".git", ".idea", ".vscode", "node_modules"}


def should_skip(path):
    """Skip system / environment folders"""
    for part in path.split(os.sep):
        if part in EXCLUDE_DIRS:
            return True
    return False


def process_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        print(f"❌ Skipped (read error): {filepath}")
        return

    modified = False
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # 🔍 Match exact injected print (ignore whitespace)
        if line.strip() == TARGET_LINE:

            # Check if already wrapped (look at previous line)
            if i > 0 and "__main__" in lines[i - 1]:
                new_lines.append(line)
                i += 1
                continue

            # Replace with safe block
            new_lines.extend(REPLACEMENT_LINES)
            modified = True
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if modified:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"✅ Fixed: {filepath}")
        except Exception:
            print(f"❌ Failed to write: {filepath}")
    else:
        print(f"➖ No change: {filepath}")


def run():
    root = os.getcwd()

    print(f"\n🔧 Fixing runtime signature prints in: {root}\n")

    for dirpath, dirnames, filenames in os.walk(root):

        if should_skip(dirpath):
            continue

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                process_file(filepath)

    print("\n✅ Done.\n")


if __name__ == "__main__":
    run()