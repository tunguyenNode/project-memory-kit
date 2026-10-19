"""Reproducible synthetic retrieval benchmark, no model calls or network."""
import json
import platform
from pathlib import Path
import statistics
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_memory import Harness, MemoryStore, Observation


def median_ms(fn, repeats=30):
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        timings.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(timings), 3)


def main():
    with tempfile.TemporaryDirectory(prefix="synthetic-memory-benchmark-") as temp:
        with MemoryStore(str(Path(temp) / "benchmark.db")) as store:
            store.create_project("synthetic")
            harness = Harness(store)
            for index in range(1000):
                harness.record_observation("synthetic", Observation(
                    f"fixture-{index}", "Synthetic unrelated planning detail " * 8,
                    f"synthetic:fixture-{index}"))
            old = harness.record_decision("synthetic", Observation("storage", "Use JSON files", "synthetic:decision-1"))
            current = harness.record_decision("synthetic", Observation("storage", "Use SQLite", "synthetic:decision-2"), supersedes=old, reason="Need atomic writes")
            baseline = lambda: json.dumps(store.search("synthetic", include_history=True), ensure_ascii=True, separators=(",", ":"))
            selective = lambda: harness.session_start("synthetic", query="storage", budget=4000)
            full = baseline()
            pack = selective()
            full_rows = json.loads(full)
            selected = json.loads(pack)["entries"]
            assert [row["id"] for row in selected] == [current]
            assert len(pack) <= 4000
            report = {
                "scenario": "1000 unrelated synthetic facts plus one superseded decision and its replacement",
                "python": platform.python_version(),
                "storage": "temporary on-disk SQLite; single process; warm repeated reads",
                "repeats": 30,
                "budget_chars": 4000,
                "naive_full_history": {"bytes_utf8": len(full.encode()), "records": len(full_rows), "includes_superseded": any(row["id"] == old for row in full_rows), "median_retrieval_serialization_ms": median_ms(baseline)},
                "harness_query_pack": {"bytes_utf8": len(pack.encode()), "records": len(selected), "selected_expected_current_id": [row["id"] for row in selected] == [current], "includes_superseded": any(row["id"] == old for row in selected), "median_retrieval_serialization_ms": median_ms(selective)},
                "context_byte_reduction_percent": round((1 - len(pack.encode()) / len(full.encode())) * 100, 2),
                "limits": "One easy lexical synthetic fixture, not a real-agent accuracy or speed test. Both methods scan rows; harness also scans for warnings. No LLM latency, tokens, cost or quality measured. Baseline is naive full history, not a tuned competitor or maintained Markdown handoff. Timing varies by machine."
            }
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
