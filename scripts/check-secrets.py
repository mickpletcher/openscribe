import json
import subprocess
import sys
from hashlib import sha1
from pathlib import Path

inventory = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                           capture_output=True, text=True, check=True)
paths = [path for path in inventory.stdout.split("\0") if path]
result = subprocess.run([sys.executable, "-m", "detect_secrets", "scan", "--no-verify", *paths],
                        capture_output=True, text=True, check=False)
if result.returncode:
    print("Secret scanner failed to execute.")
    sys.exit(result.returncode)
findings = json.loads(result.stdout).get("results", {})
baseline = json.loads(Path(".secrets.baseline").read_text(encoding="utf-8"))
if baseline.get("version") != 1:
    raise ValueError("Unsupported secret review baseline version.")
reviewed = {(item["path"], item["type"], item["hash"]) for item in baseline["reviewed_false_positives"]}
reviewed.update((".secrets.baseline", "Hex High Entropy String", sha1(item["hash"].encode(), usedforsecurity=False).hexdigest())
                for item in baseline["reviewed_false_positives"])
findings = {
    path: [item for item in items if (path.replace("\\", "/"), item["type"], item["hashed_secret"]) not in reviewed]
    for path, items in findings.items()
}
findings = {path: items for path, items in findings.items() if items}
if findings:
    print(f"Secret scan requires review: {sum(len(items) for items in findings.values())} findings in {len(findings)} files.")
    for path in findings:
        print(path)
    sys.exit(1)
print("Secret scan: no unreviewed findings.")
