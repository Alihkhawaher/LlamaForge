import conftest_paths  # noqa: F401
import unittest
import anthropic_shim as sh


class TestErrorMapping(unittest.TestCase):
    def test_error_envelope_shape(self):
        status, body = sh.anthropic_error(404, "not_found_error", "no model")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"type": "error", "error": {"type": "not_found_error", "message": "no model"}})

    def test_status_classification(self):
        self.assertEqual(sh.error_type_for_status(404), "not_found_error")
        self.assertEqual(sh.error_type_for_status(400), "invalid_request_error")
        self.assertEqual(sh.error_type_for_status(422), "invalid_request_error")
        self.assertEqual(sh.error_type_for_status(500), "api_error")
        self.assertEqual(sh.error_type_for_status(599), "overloaded_error")
        self.assertEqual(sh.error_type_for_status(529), "overloaded_error")


if __name__ == "__main__":
    unittest.main()
