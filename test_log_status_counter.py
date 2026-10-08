"""Tests for log_status_counter.py"""
import csv
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from log_status_counter import (
    class_of, count_statuses, parse_line, to_csv, to_json, to_text,
)

GOOD_200 = ('203.0.113.7 - - [08/Oct/2026:10:15:32 +0500] '
            '"GET /about HTTP/1.1" 200 4521 "-" "Mozilla/5.0"')
GOOD_404 = ('198.51.100.23 - - [08/Oct/2026:10:16:01 +0500] '
            '"GET /missing HTTP/1.1" 404 512 "-" "curl/8.5.0"')
GOOD_500 = ('192.0.2.9 - - [08/Oct/2026:10:17:44 +0500] '
            '"POST /api/contact HTTP/1.1" 500 1024 "-" "Mozilla/5.0"')
BAD_1 = "this is not a log line"
BAD_2 = "203.0.113.9 - - broken [timestamp"


class TestLogStatusCounter(unittest.TestCase):
    def test_parse_valid_line(self):
        self.assertEqual(parse_line(GOOD_200), 200)
        self.assertEqual(parse_line(GOOD_404), 404)

    def test_parse_malformed_returns_none(self):
        self.assertIsNone(parse_line(BAD_1))
        self.assertIsNone(parse_line(BAD_2))
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("   "))

    def test_count_mixed_lines(self):
        lines = [GOOD_200, GOOD_200, GOOD_404, GOOD_500, BAD_1, BAD_2, ""]
        counter, unparsed = count_statuses(lines)
        self.assertEqual(counter[200], 2)
        self.assertEqual(counter[404], 1)
        self.assertEqual(counter[500], 1)
        self.assertEqual(unparsed, 2)  # blank line skipped, not counted

    def test_blank_lines_ignored(self):
        counter, unparsed = count_statuses(["", "   ", "\n"])
        self.assertEqual(sum(counter.values()), 0)
        self.assertEqual(unparsed, 0)

    def test_class_of(self):
        self.assertEqual(class_of(200), "2xx")
        self.assertEqual(class_of(301), "3xx")
        self.assertEqual(class_of(404), "4xx")
        self.assertEqual(class_of(503), "5xx")
        self.assertEqual(class_of(101), "1xx")

    def test_text_output_structure(self):
        counter, unparsed = count_statuses([GOOD_200, GOOD_404, GOOD_500, BAD_1])
        out = to_text(counter, unparsed)
        self.assertIn("Total requests: 3", out)
        self.assertIn("Unparsed lines: 1", out)
        self.assertIn("200", out)
        self.assertIn("2xx", out)
        self.assertIn("4xx", out)
        self.assertIn("5xx", out)

    def test_min_count_hides_rare(self):
        counter, unparsed = count_statuses([GOOD_200, GOOD_200, GOOD_404])
        out = to_text(counter, unparsed, min_count=2)
        self.assertIn("200", out)
        self.assertNotIn("404", out.split("By class:")[0])

    def test_csv_output(self):
        counter, unparsed = count_statuses([GOOD_200, GOOD_404, BAD_1])
        rows = list(csv.DictReader(to_csv(counter, unparsed).splitlines()))
        codes = {r["status_code"]: int(r["count"]) for r in rows}
        self.assertEqual(codes["200"], 1)
        self.assertEqual(codes["404"], 1)
        self.assertEqual(codes["unparsed"], 1)

    def test_json_output(self):
        counter, unparsed = count_statuses([GOOD_200, GOOD_404, BAD_1])
        data = json.loads(to_json(counter, unparsed))
        self.assertEqual(data["total_requests"], 2)
        self.assertEqual(data["unparsed_lines"], 1)
        by_status = {d["code"]: d["count"] for d in data["by_status"]}
        self.assertEqual(by_status[200], 1)
        by_class = {d["class"]: d["count"] for d in data["by_class"]}
        self.assertEqual(by_class["2xx"], 1)
        self.assertEqual(by_class["4xx"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
