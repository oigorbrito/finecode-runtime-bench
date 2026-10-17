import unittest
from token_usage import aggregate

BASE = dict(run_id="r", task_id="python-1", variant="pi", request_index=0)

class UsageTests(unittest.TestCase):
    def test_totals(self):
        rows = [dict(BASE, input_tokens=12, output_tokens=4, cache_read_tokens=2), dict(BASE, request_index=1, input_tokens=8, output_tokens=3, cache_read_tokens=1)]
        result = aggregate(rows)[0]
        self.assertEqual((result["input_tokens"], result["output_tokens"], result["cache_read_tokens"]), (20, 7, 3))
        self.assertTrue(result["usage_complete"])
        self.assertIsNone(result["reasoning_tokens"])

    def test_missing_usage_not_zero(self):
        result = aggregate([dict(BASE, input_tokens=10)])[0]
        self.assertIsNone(result["output_tokens"])
        self.assertFalse(result["usage_complete"])

    def test_duplicate_request_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            aggregate([BASE, BASE])

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([dict(BASE, input_tokens=-1)])

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([dict(BASE, input_tokens=True)])

    def test_variant_isolation(self):
        result = aggregate([dict(BASE, input_tokens=5, output_tokens=2), dict(BASE, variant="bolt", input_tokens=6, output_tokens=2)])
        self.assertEqual(len(result), 2)

if __name__ == "__main__":
    unittest.main()
