"""Maintainability guard (#005 1f): no source file exceeds the line cap.

The run.py monolith (1048 lines) is what motivated the 1a/1f router split; this test keeps any
single file from drifting back toward that. The cap is enforced here as a test (CI enforcement is
deferred). If a file legitimately needs to exceed the cap, split it — don't raise the cap.
"""
import os

CAP = 400
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ["realify", "tests"]
SCAN_ROOT_FILES = ["run.py"]


def _py_files():
    files = [os.path.join(ROOT, f) for f in SCAN_ROOT_FILES]
    for d in SCAN_DIRS:
        for dirpath, _dirs, names in os.walk(os.path.join(ROOT, d)):
            if "__pycache__" in dirpath:
                continue
            files += [os.path.join(dirpath, n) for n in names if n.endswith(".py")]
    return files


def test_no_file_exceeds_line_cap():
    offenders = []
    for path in _py_files():
        with open(path, encoding="utf-8") as fh:
            n = sum(1 for _ in fh)
        if n > CAP:
            offenders.append((os.path.relpath(path, ROOT), n))
    offenders.sort(key=lambda x: -x[1])
    assert not offenders, (
        f"files over the {CAP}-line cap (split them, don't raise the cap): {offenders}"
    )


if __name__ == "__main__":
    test_no_file_exceeds_line_cap()
    print("file-length cap OK")
