import json
import tempfile
import unittest
from pathlib import Path

from pipeline.ingestao.mock_support import append_mock_message, read_mock_messages, write_mock_csv


class MockSupportTests(unittest.TestCase):
    def test_write_mock_csv_creates_file_with_expected_columns(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "mock.csv"
            write_mock_csv(output_path, table_name="alfabetizacao")

            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("NU_ANO", content)
            self.assertIn("IN_ALFABETIZADO", content)

    def test_append_and_read_mock_messages_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "messages.jsonl"
            payload = {"tipo_mensagem": "dados_aluno", "ID_ALUNO": 123}

            append_mock_message(output_path, payload)
            messages = read_mock_messages(output_path)

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["tipo_mensagem"], "dados_aluno")
            self.assertEqual(messages[0]["ID_ALUNO"], 123)


if __name__ == "__main__":
    unittest.main()
