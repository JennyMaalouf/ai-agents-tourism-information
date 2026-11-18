import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.emissions_retrieval import load_test_chunks, search_test_chunks


class EmissionsRetrievalTests(unittest.TestCase):
    def test_retrieves_relevant_report_and_keeps_filename_citation(self):
        chunks = load_test_chunks()

        results = search_test_chunks("thermal aging THC conversion decrease", chunks)

        self.assertTrue(results)
        self.assertEqual(results[0].source, "CAT-202.txt")
        retrieved_text = "\n".join(result.text for result in results)
        self.assertIn("14 percentage points", retrieved_text)

    def test_no_match_does_not_return_unrelated_reports(self):
        self.assertEqual(search_test_chunks("volcano rainfall", []), [])

    def test_loads_only_text_reports_from_data_directory(self):
        with TemporaryDirectory() as directory:
            data_dir = Path(directory)
            (data_dir / "TEST.txt").write_text(
                "Title: Sample test\n\nMeasured catalyst conversion was 80%.",
                encoding="utf-8",
            )
            (data_dir / "ignored.md").write_text("not a report", encoding="utf-8")

            chunks = load_test_chunks(data_dir)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source, "TEST.txt")


if __name__ == "__main__":
    unittest.main()
