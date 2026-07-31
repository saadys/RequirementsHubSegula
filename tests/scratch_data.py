from textwrap import indent
import json
from backend.config import HISTORIC_PROJECTS_PATH

with open(HISTORIC_PROJECTS_PATH) as f:
    projects = json.load(f)

print(f"Loaded {len(projects)} projects")
for p in projects:
    print(f"  - {p['project_name']} ({p['department']}) tags: {p['tags']}")

assert len(projects) == 4