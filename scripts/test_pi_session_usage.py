import unittest
from pi_session_usage import convert
import json

def entry(role, usage=None):
    return json.dumps({"type":"message","message":{"role":role,"content":[{"type":"text","text":"PRIVATE"}],**({"usage":usage} if usage is not None else {})}})

class PiSessionTests(unittest.TestCase):
    def parse(self, lines):
        return list(convert(lines,run_id="r",task_id="t",variant="pi"))

    def test_real_pi_usage_shape(self):
        usage={"input":11,"output":7,"cacheRead":3,"cacheWrite":2,"reasoning":1,"totalTokens":23,"cost":{"total":0.01}}
        result=self.parse([json.dumps({"type":"session","version":3}),entry("user"),entry("assistant",usage)])[0]
        self.assertEqual((result["input_tokens"],result["output_tokens"],result["reasoning_tokens"]),(11,7,1))
        self.assertNotIn("content",result)
        self.assertNotIn("PRIVATE",json.dumps(result))

    def test_missing_reasoning_remains_null(self):
        result=self.parse([entry("assistant",{"input":1,"output":2})])[0]
        self.assertIsNone(result["reasoning_tokens"])

    def test_missing_usage_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"without usage"):
            self.parse([entry("assistant")])

    def test_no_assistant_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"no assistant"):
            self.parse([entry("user")])

    def test_sequential_request_ids(self):
        result=self.parse([entry("assistant",{"input":1}),entry("assistant",{"input":2})])
        self.assertEqual([x["request_index"] for x in result],[0,1])

if __name__=="__main__":
    unittest.main()
