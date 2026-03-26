from __future__ import annotations

import unittest

from common import EVAL_SCORE_DIMENSIONS, build_eval_result_schema


class EvalSchemaTest(unittest.TestCase):
    def test_build_eval_result_schema_uses_task_scoped_fixed_score_keys(self) -> None:
        for task_name, dimensions in EVAL_SCORE_DIMENSIONS.items():
            with self.subTest(task=task_name):
                schema = build_eval_result_schema(task_name)
                score_keys = [key for key, _ in dimensions]

                self.assertEqual(schema["required"], list(schema["properties"].keys()))
                self.assertEqual(schema["properties"]["source_format"]["enum"], ["json"])

                scores = schema["properties"]["scores"]
                self.assertFalse(scores["additionalProperties"])
                self.assertNotIn("minProperties", scores)
                self.assertEqual(scores["required"], score_keys)
                self.assertEqual(list(scores["properties"].keys()), score_keys)

                feedback = schema["properties"]["dimension_feedback"]
                self.assertFalse(feedback["additionalProperties"])
                self.assertEqual(feedback["required"], score_keys)
                self.assertEqual(list(feedback["properties"].keys()), score_keys)


if __name__ == "__main__":
    unittest.main()
