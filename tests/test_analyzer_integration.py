import unittest
import os
import json
import shutil
import tempfile
import sys
import re
from unittest.mock import MagicMock

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.analyze.analyzor import run_analysis, nlp_global as anlz_nlp_global

def get_test_data_path(subfolder, filename):
    return os.path.join(TEST_DIR, "test_data", subfolder, filename)

from src.analyze.analyzor import run_analysis, nlp_global as anlz_nlp_global

def assert_json_almost_equal(test_case, generated, expected, places=7, msg=None, path="root", 
                             list_length_tolerances=None, 
                             ignore_content_if_length_tolerant_paths=None,
                             ignore_exact_value_at_paths=None):
    """
    Vergleicht rekursiv JSON-ähnliche Strukturen.
    - Verwendet assertAlmostEqual für Fließkommazahlen.
    - Erlaubt Längentoleranz für Listen via list_length_tolerances.
    - Erlaubt das Ignorieren des Inhaltsvergleichs für Listen (deren Länge im Toleranzbereich ist)
      via ignore_content_if_length_tolerant_paths.
    - Erlaubt das Ignorieren des exakten Wertvergleichs für spezifische Pfade (für Nicht-Listen/Dicts/Floats)
      via ignore_exact_value_at_paths.
    """
    type_gen = type(generated)
    type_exp = type(expected)

    if type_gen != type_exp:
        error_msg = f"{msg or ''} Type mismatch at '{path}': expected {type_exp.__name__}, got {type_gen.__name__}."
        test_case.fail(error_msg)

    if isinstance(generated, dict):
        if set(generated.keys()) != set(expected.keys()):
            error_msg = f"{msg or ''} Key mismatch at '{path}': expected {set(expected.keys())}, got {set(generated.keys())}."
            test_case.fail(error_msg)
        
        for k in generated:
            assert_json_almost_equal(test_case, generated[k], expected[k], places, msg, path=f"{path}.{k}", 
                                     list_length_tolerances=list_length_tolerances,
                                     ignore_content_if_length_tolerant_paths=ignore_content_if_length_tolerant_paths,
                                     ignore_exact_value_at_paths=ignore_exact_value_at_paths)
    elif isinstance(generated, list):
        length_tolerance = 0
        matched_length_tolerance_path = None
        
        if list_length_tolerances:
            if path in list_length_tolerances:
                length_tolerance = list_length_tolerances[path]
                matched_length_tolerance_path = path
            else:
                for t_path, t_val in list_length_tolerances.items():
                    if "[*]" in t_path:
                        placeholder = "###JSON_PATH_WILDCARD_LEN###"
                        temp_path_for_regex = t_path.replace("[*]", placeholder)
                        escaped_temp_path = re.escape(temp_path_for_regex)
                        regex_pattern = "^" + escaped_temp_path.replace(re.escape(placeholder), r"\[\d+\]") + "$"
                        if re.match(regex_pattern, path):
                            length_tolerance = t_val
                            matched_length_tolerance_path = t_path
                            break
        
        apply_ignore_content_rule = False
        matched_ignore_content_path_rule = None
        if ignore_content_if_length_tolerant_paths:
            if path in ignore_content_if_length_tolerant_paths:
                apply_ignore_content_rule = True
                matched_ignore_content_path_rule = path
            else:
                for ignore_pattern in ignore_content_if_length_tolerant_paths:
                    if "[*]" in ignore_pattern:
                        placeholder = "###JSON_PATH_WILDCARD_IGNORE_CONTENT###"
                        temp_path_for_regex = ignore_pattern.replace("[*]", placeholder)
                        escaped_temp_path = re.escape(temp_path_for_regex)
                        regex_pattern = "^" + escaped_temp_path.replace(re.escape(placeholder), r"\[\d+\]") + "$"
                        if re.match(regex_pattern, path):
                            apply_ignore_content_rule = True
                            matched_ignore_content_path_rule = ignore_pattern
                            break
                            
        actual_length_diff = abs(len(generated) - len(expected))
        
        if actual_length_diff > length_tolerance:
            error_msg = f"{msg or ''} List length mismatch at '{path}': expected {len(expected)}, got {len(generated)} (allowed difference {length_tolerance} based on rule '{matched_length_tolerance_path or 'N/A'}')."
            test_case.fail(error_msg)
        elif apply_ignore_content_rule:
            return
        else:
            len_to_compare = min(len(generated), len(expected))
            for i in range(len_to_compare):
                assert_json_almost_equal(test_case, generated[i], expected[i], places, msg, path=f"{path}[{i}]",
                                         list_length_tolerances=list_length_tolerances,
                                         ignore_content_if_length_tolerant_paths=ignore_content_if_length_tolerant_paths,
                                         ignore_exact_value_at_paths=ignore_exact_value_at_paths)
    elif isinstance(generated, float):
        try:
            test_case.assertAlmostEqual(generated, expected, places=places)
        except AssertionError as e:
            error_msg = f"{msg or ''} Float mismatch at '{path}': {e}"
            test_case.fail(error_msg)
    else:
        if ignore_exact_value_at_paths:
            if path in ignore_exact_value_at_paths:
                return
            for ignore_pattern in ignore_exact_value_at_paths:
                if "[*]" in ignore_pattern:
                    placeholder = "###JSON_PATH_WILDCARD_IGNORE_VALUE###"
                    temp_path_for_regex = ignore_pattern.replace("[*]", placeholder)
                    escaped_temp_path = re.escape(temp_path_for_regex)
                    regex_pattern = "^" + escaped_temp_path.replace(re.escape(placeholder), r"\[\d+\]") + "$"
                    if re.match(regex_pattern, path):
                        return
        try:
            test_case.assertEqual(generated, expected)
        except AssertionError as e:
            error_msg = f"{msg or ''} Value mismatch at '{path}': {e}"
            test_case.fail(error_msg)

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

        tolerances = {
            "root.news_segments[*].sentences": 15,
            "root.news_segments": 15,

            "root.traffic_report_segments[*].sentences": 15,
            "root.traffic_report_segments": 15,

            "root.conversation_segments": 30,
            "root.conversation_segments[*].sentences": 30,
            
            "root.weather_report_segments[*].sentences": 15,
            "root.weather_report_segments": 15,  
        }

        paths_to_ignore_content_if_length_ok = {
            "root.news_segments[*].sentences",
            "root.traffic_report_segments[*].sentences",
            "root.conversation_segments[*].sentences",
            "root.weather_report_segments[*].sentences",
        }
        
        paths_to_ignore_exact_value = {
            "root.conversation_segments[*].estimated_report_time",
            "root.conversation_segments[*].segment_start_char_offset",
            "root.conversation_segments[*].segment_end_char_offset",
        }
        try:
             assert_json_almost_equal(self, generated_data, expected_data, places=15, 
                                    msg=f"Inhalt der generierten JSON für '{expected_json_filename}' stimmt nicht mit Erwartung überein.",
                                    list_length_tolerances=tolerances,
                                    ignore_content_if_length_tolerant_paths=paths_to_ignore_content_if_length_ok,
                                    ignore_exact_value_at_paths=paths_to_ignore_exact_value)
        except AssertionError as e:
            self.fail(f"AssertionError in assert_json_almost_equal: {e}")
        print(f"Erfolgreich verifiziert: {expected_json_filename}")

    def test_negative_intentional_mismatch(self):
        """
        Testet, ob assert_json_almost_equal bei stark abweichenden JSON-Strukturen fehlschlägt.
        """
        transcript_file = "dummy_mismatch_test.txt"
        expected_json_file = "dummy_mismatch_test_analysis.json"
        
        source_transcript_path = get_test_data_path("sample_transcripts", transcript_file)
        if not os.path.exists(source_transcript_path):
            self.skipTest(f"Dummy transcript '{transcript_file}' für Negativtest nicht gefunden.")
            return
        
        expected_json_path = get_test_data_path("expected_json_outputs", expected_json_file)
        if not os.path.exists(expected_json_path):
            self.skipTest(f"Dummy expected JSON '{expected_json_file}' für Negativtest nicht gefunden.")
            return
        with self.assertRaises(AssertionError, msg="assert_json_almost_equal sollte bei stark unterschiedlichen JSONs einen Fehler auslösen."):
            self._perform_test_for_file(transcript_file, expected_json_file)
        
        print(f"Negativtest '{self.test_negative_intentional_mismatch.__name__}' erfolgreich: AssertionError wie erwartet ausgelöst.")

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

    def test_process_swr3_20250516_000318_20250516_010317(self):
        self._perform_test_for_file(
            "swr3_20250516_000318_20250516_010317.txt",
            "swr3_20250516_000318_20250516_010317_analysis.json"
        )

    def test_process_wdr2_20250516_210012_20250516_220011(self):
         self._perform_test_for_file(
             "wdr2_20250516_210012_20250516_220011.txt",
             "wdr2_20250516_210012_20250516_220011_analysis.json"
         )

    def test_process_wdr2_20250516_220011_20250516_230009(self):
         self._perform_test_for_file(
             "wdr2_20250516_220011_20250516_230009.txt",
             "wdr2_20250516_220011_20250516_230009_analysis.json"
         )

if __name__ == '__main__':
    unittest.main()