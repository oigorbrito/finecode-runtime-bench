import unittest
from compare_token_usage import compare

def row(variant,total,run="r",task="t",complete=True):
    return {"run_id":run,"task_id":task,"variant":variant,"input_tokens":total-3,
            "output_tokens":3,"provider_reported_total_tokens":total,"usage_complete":complete}

class ComparisonTests(unittest.TestCase):
    def test_paired_delta(self):
        r=compare([row("pi",100),row("bolt",80)],"pi","bolt")
        self.assertEqual(r[0]["candidate_delta_pct"],-20)

    def test_missing_pair_fails(self):
        with self.assertRaisesRegex(ValueError,"unpaired"):
            compare([row("pi",100)],"pi","bolt")

    def test_missing_usage_fails(self):
        x=row("bolt",80);x["provider_reported_total_tokens"]=None
        with self.assertRaisesRegex(ValueError,"missing"):
            compare([row("pi",100),x],"pi","bolt")

    def test_incomplete_usage_fails(self):
        with self.assertRaisesRegex(ValueError,"incomplete"):
            compare([row("pi",100),row("bolt",80,complete=False)],"pi","bolt")

    def test_zero_baseline_fails(self):
        with self.assertRaisesRegex(ValueError,"positive"):
            compare([row("pi",0),row("bolt",80)],"pi","bolt")

    def test_duplicate_fails(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            compare([row("pi",100),row("pi",100),row("bolt",80)],"pi","bolt")

if __name__=="__main__":
    unittest.main()
