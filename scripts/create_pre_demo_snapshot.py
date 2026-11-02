import hashlib
import os
import subprocess
from pathlib import Path

def main():
    snapshot_dir = Path("data/snapshots/pre_demo_20261101")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # 1. Git diff patch
    diff_res = subprocess.check_output(["git", "diff"])
    with open(snapshot_dir / "pre_demo_working_tree.patch", "wb") as f:
        f.write(diff_res)

    # 2. Git status
    status_res = subprocess.check_output(["git", "status"])
    with open(snapshot_dir / "pre_demo_git_status.txt", "wb") as f:
        f.write(status_res)

    # 3. File hashes
    files_out = subprocess.check_output(["git", "diff", "--name-only"]).decode("utf-8").splitlines()
    files = [f.strip() for f in files_out if f.strip()]
    benchmark_file = "data/benchmark/aeris_benchmark.json"
    if benchmark_file not in files and os.path.exists(benchmark_file):
        files.append(benchmark_file)

    lines = []
    print("Pre-demo file hashes (SHA-256):")
    for f in sorted(files):
        if os.path.exists(f):
            h = hashlib.sha256(open(f, "rb").read()).hexdigest()
            line = f"{h}  {f}"
            lines.append(line)
            print(f"  {line}")

    with open(snapshot_dir / "pre_demo_file_hashes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nSnapshot successfully created in: {snapshot_dir}")

if __name__ == "__main__":
    main()
