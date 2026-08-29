import json
import unittest
from moodle_bot.moodle.courses import normalize_course, compute_stable_hash
from moodle_bot.moodle.tracker import extract_course_delta
from moodle_bot.config import CACHE_DIR


class TestNormalizedDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache_file = CACHE_DIR / "5.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cls.sample_data = json.load(f)
        else:
            # Self-contained fallback mock course data
            cls.sample_data = [
                {
                    "id": 1,
                    "name": "General",
                    "section": 0,
                    "modules": [
                        {
                            "id": 101,
                            "name": "Welcome Notice",
                            "modname": "forum",
                            "contents": [],
                        },
                        {
                            "id": 102,
                            "name": "Lecture 1 Slides",
                            "modname": "resource",
                            "contents": [
                                {
                                    "filename": "lecture1.pdf",
                                    "filesize": 1024,
                                    "timemodified": 1600000000,
                                    "fileurl": "https://moodle.test/pluginfile.php/1/lecture1.pdf?forcedownload=1&token=123",
                                }
                            ],
                        },
                    ],
                }
            ]

    def test_normalization(self):
        norm = normalize_course(self.sample_data)
        self.assertIsInstance(norm, dict, "Normalized output must be a dictionary")
        self.assertGreater(len(norm), 0, "Normalized dictionary should not be empty")

    def test_stable_hashing(self):
        norm = normalize_course(self.sample_data)
        hash1 = compute_stable_hash(norm)
        hash2 = compute_stable_hash(norm)
        self.assertEqual(hash1, hash2, "Hashing must be deterministic and stable")

    def test_delta_self_comparison(self):
        norm = normalize_course(self.sample_data)
        delta_self = extract_course_delta(norm, norm)
        self.assertEqual(len(delta_self["added"]), 0)
        self.assertEqual(len(delta_self["updated"]), 0)
        self.assertEqual(len(delta_self["removed"]), 0)

    def test_delta_simulated_added_item(self):
        norm = normalize_course(self.sample_data)
        norm_simulated = dict(norm)
        norm_simulated["99999"] = {
            "module_id": 99999,
            "name": "Simulated Quiz",
            "modname": "quiz",
            "section_name": "General",
        }
        delta_sim = extract_course_delta(norm, norm_simulated)
        self.assertEqual(len(delta_sim["added"]), 1)
        self.assertEqual(delta_sim["added"][0]["name"], "Simulated Quiz")


if __name__ == "__main__":
    unittest.main()
