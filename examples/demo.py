"""Entirely synthetic demo; all storage lives in a temporary directory."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_memory import MemoryStore


def main():
    with tempfile.TemporaryDirectory(prefix="synthetic-memory-demo-") as temp:
        path = str(Path(temp) / "demo.sqlite3")
        with MemoryStore(path) as memory:
            memory.create_project("synthetic-garden")
            memory.create_project("synthetic-other")
            first = memory.add("synthetic-garden", "decision", "storage", "Use JSON files",
                               "synthetic:meeting-1", observed_at="2020-01-01T00:00:00Z")
            memory.add("synthetic-garden", "decision", "storage", "Use SQLite for atomic writes",
                       "synthetic:meeting-2", supersedes=first, reason="Need atomic updates")
            memory.add("synthetic-garden", "task", "prototype", "Build a synthetic seed inventory",
                       "synthetic:brief", review_after="2020-01-01T00:00:00Z")
            memory.add("synthetic-garden", "fact", "capacity", "Plan for 20 beds", "synthetic:plan-a")
            memory.add("synthetic-garden", "fact", "capacity", "Plan for 30 beds", "synthetic:plan-b")
            print("Decision history:")
            print(json.dumps(memory.history("synthetic-garden", first), indent=2))
            print("Review warnings:")
            print(json.dumps(memory.warnings("synthetic-garden"), indent=2))
            assert memory.search("synthetic-other") == []
        # A new connection represents the next agent session.
        with MemoryStore(path) as memory:
            print("Next-session context (max 3000 characters):")
            context = memory.export_context("synthetic-garden", max_chars=3000)
            assert len(context) <= 3000
            print(context)
    print("Synthetic demo passed. Temporary database removed.")


if __name__ == "__main__":
    main()
