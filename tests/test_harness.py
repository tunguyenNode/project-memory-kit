import json
import unittest
from project_memory import Harness, MemoryStore, Observation, SecretDetected


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.store.create_project("demo")
        self.harness = Harness(self.store)

    def tearDown(self):
        self.store.close()

    def test_session_hooks_and_checkpoint_history(self):
        self.harness.record_observation("demo", Observation("goal", "Synthetic goal", "synthetic:brief"))
        first = self.harness.record_decision("demo", Observation("storage", "JSON", "synthetic:design"))
        self.harness.record_decision("demo", Observation("storage", "SQLite", "synthetic:revision"), supersedes=first, reason="Atomic writes")
        checkpoint = self.harness.session_end("demo", summary="Prototype built", next_step="Run tests", source="synthetic:session-1")
        self.harness.session_end("demo", summary="Tests passed", next_step="Review", source="synthetic:session-2")
        self.assertEqual(len(self.store.history("demo", checkpoint)), 2)
        context = json.loads(self.harness.session_start("demo", "storage", 2000))
        self.assertEqual(context["entries"][0]["content"], "SQLite")
        self.assertEqual(len(context["entries"]), 1)

    def test_explicit_schema_and_secret_guard(self):
        with self.assertRaises(ValueError):
            self.harness.record_observation("demo", "raw chat")
        with self.assertRaises(SecretDetected):
            self.harness.session_end("demo", summary="password=synthetic-secret", next_step="Review", source="synthetic:test")
        self.assertEqual(self.store.search("demo"), [])

    def test_harness_project_isolation(self):
        self.store.create_project("other")
        self.harness.record_observation("demo", Observation("goal", "Private to project", "synthetic:brief"))
        self.assertEqual(json.loads(self.harness.session_start("other"))["entries"], [])
