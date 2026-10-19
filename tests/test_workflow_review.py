"""Independent dry-run checkpoint edge cases; synthetic state only."""
import copy
import io
from contextlib import redirect_stderr
from pathlib import Path
import tempfile
import unittest
from project_memory.workflow import Workflow, main


class WorkflowReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'workflow.json'

    def tearDown(self):
        self.temp.cleanup()

    def test_oversized_create_does_not_leave_invalid_file(self):
        with self.assertRaises(ValueError):
            Workflow.create(self.path, ['x' * 4194304], ['Synthetic criterion'])
        self.assertFalse(self.path.exists())

    def test_rejected_edit_preserves_in_memory_and_disk_state(self):
        flow = Workflow.create(self.path, ['Synthetic scope'], ['Synthetic criterion'])
        before = copy.deepcopy(flow.data)
        disk = self.path.read_bytes()
        with self.assertRaises(ValueError):
            flow.edit([], ['Synthetic criterion'])
        self.assertEqual(flow.data, before)
        self.assertEqual(self.path.read_bytes(), disk)

    def test_top_level_list_is_clean_schema_error(self):
        self.path.write_text('[]')
        with redirect_stderr(io.StringIO()) as errors:
            code = main(['show', str(self.path)])
        self.assertEqual(code, 2)
        self.assertNotIn('Traceback', errors.getvalue())

    def test_stale_writer_cannot_overwrite_newer_state(self):
        initial = Workflow.create(self.path, ['Synthetic scope'], ['Synthetic criterion'])
        stale = Workflow(self.path)
        initial.submit()
        latest = self.path.read_bytes()
        with self.assertRaises(ValueError):
            stale.edit(['Different synthetic scope'], ['Different criterion'])
        self.assertEqual(self.path.read_bytes(), latest)


if __name__ == '__main__':
    unittest.main()
