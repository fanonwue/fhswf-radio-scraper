import unittest
import os
import json
import shutil
import tempfile
import sys
from unittest.mock import MagicMock

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.analyze.analyzor import run_analysis, nlp_global as anlz_nlp_global

def get_test_data_path(subfolder, filename):
    return os.path.join(TEST_DIR, "test_data", subfolder, filename)

class TestAnalyzerIntegration(unittest.TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        cls.nlp_model_for_test = anlz_nlp_global 
        if cls.nlp_model_for_test:
            print("Test Class: spaCy model 'de_core_news_lg' (aus analyzor) wird verwendet.")
        else:
            print("Test Class: spaCy model 'de_core_news_lg' (aus analyzor) nicht geladen. Test prüft Fallback.")

    def setUp(self):
        self.temp_input_dir = tempfile.mkdtemp(prefix="test_analyzer_input_")
        self.temp_output_dir = tempfile.mkdtemp(prefix="test_analyzer_output_")
        self.path_to_generated_json = None

    def tearDown(self):
        shutil.rmtree(self.temp_input_dir)
        shutil.rmtree(self.temp_output_dir)

    def _perform_test_for_file(self, transcript_filename, expected_json_filename):
        source_transcript_path = get_test_data_path("sample_transcripts", transcript_filename)
        if not os.path.exists(source_transcript_path):
            self.skipTest(f"Test transcript '{transcript_filename}' not found.")
            return

        staged_transcript_path = os.path.join(self.temp_input_dir, transcript_filename)
        shutil.copyfile(source_transcript_path, staged_transcript_path)

        self.path_to_generated_json = os.path.join(self.temp_output_dir, expected_json_filename)

        current_nlp_model_to_use = self.nlp_model_for_test
        mock_nlp = None
        if not current_nlp_model_to_use:
            mock_nlp = MagicMock()
            mock_nlp.vocab = MagicMock()
            current_nlp_model_to_use = mock_nlp
            print(f"Testing with mocked NLP model for {transcript_filename} as global model is None.")

        success = run_analysis(
            input_transcript_dir=self.temp_input_dir,
            output_analysis_dir=self.temp_output_dir,
            nlp_model=current_nlp_model_to_use
        )

        if not self.nlp_model_for_test:
            self.assertFalse(success, "run_analysis sollte False zurückgeben, wenn kein NLP-Modell vorhanden ist.")
            self.assertFalse(os.path.exists(self.path_to_generated_json),
                             "Keine JSON-Datei sollte erstellt werden, wenn kein NLP-Modell vorhanden ist.")
            print(f"Test für {transcript_filename} ohne NLP-Modell erfolgreich (keine Ausgabe, Rückgabe False).")
            return
        else:
            self.assertTrue(success, "run_analysis sollte True zurückgeben, wenn die Verarbeitung erfolgreich war.")


        self.assertTrue(os.path.exists(self.path_to_generated_json),
                        f"Generierte JSON-Datei nicht gefunden: '{self.path_to_generated_json}'")

        expected_json_path = get_test_data_path("expected_json_outputs", expected_json_filename)
        if not os.path.exists(expected_json_path):
            self.fail(f"Erwartete JSON-Datei zum Vergleich nicht gefunden: '{expected_json_path}'")

        with open(self.path_to_generated_json, 'r', encoding='utf-8') as f_gen:
            generated_data = json.load(f_gen)
        with open(expected_json_path, 'r', encoding='utf-8') as f_exp:
            expected_data = json.load(f_exp)

        self.assertDictEqual(generated_data, expected_data,
                             f"Inhalt der generierten JSON für '{expected_json_filename}' stimmt nicht mit Erwartung überein.")
        print(f"Erfolgreich verifiziert: {expected_json_filename}")

    def test_process_swr3_20250516_210028_20250516_220026(self):
        self._perform_test_for_file(
            "swr3_20250516_210028_20250516_220026.txt",
            "swr3_20250516_210028_20250516_220026_analysis.json"
        )

    def test_process_swr3_20250516_230024(self):
        self._perform_test_for_file(
            "swr3_20250516_230024_20250517_000023.txt",
            "swr3_20250516_230024_20250517_000023_analysis.json"
        )

    def test_process_swr3_20250516_130041_20250516_140039(self):
        self._perform_test_for_file(
            "swr3_20250516_130041_20250516_140039.txt",
            "swr3_20250516_130041_20250516_140039_analysis.json"
        )

    # TODO: Schlägt manchmal fehl!
    def test_process_swr3_20250516_000318_20250516_010317(self):
        self._perform_test_for_file(
            "swr3_20250516_000318_20250516_010317.txt",
            "swr3_20250516_000318_20250516_010317_analysis.json"
        )

if __name__ == '__main__':
    unittest.main()