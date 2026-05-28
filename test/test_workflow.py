import unittest

from src.pr_function_commenter.diff import changed_lines_from_patch
from src.pr_function_commenter.extractor import extract_changed_functions
from src.pr_function_commenter.languages import language_for_path
from src.pr_function_commenter.validation import validate_comment_only_change
from src.pr_function_commenter.workflow import generate_validated_file


class WorkflowTest(unittest.TestCase):
    def test_python_ast_and_comment_only_validation_accepts_comment(self):
        language = language_for_path("math.py")
        before = "def total(a, b):\n    return a + b\n"
        after = "# Adds two values.\ndef total(a, b):\n    return a + b\n"

        valid, errors = validate_comment_only_change(before, after, language)

        self.assertTrue(valid, errors)

    def test_python_ast_validation_rejects_code_change(self):
        language = language_for_path("math.py")
        before = "def total(a, b):\n    return a + b\n"
        after = "# Adds two values.\ndef total(a, b):\n    return a - b\n"

        valid, _ = validate_comment_only_change(before, after, language)

        self.assertFalse(valid)

    def test_extracts_changed_python_function_and_adds_comment(self):
        code = "def total(a, b):\n    return a + b\n"
        patch = "@@ -0,0 +1,2 @@\n+def total(a, b):\n+    return a + b\n"
        language = language_for_path("math.py")
        functions = extract_changed_functions(code, changed_lines_from_patch(patch), language)

        result = generate_validated_file(
            file_path="math.py",
            original_code=code,
            functions=functions,
            language=language,
            comment_generator=FakeGenerator(),
            max_attempts=3,
        )
        self.assertEqual(result.status, "changed")
        self.assertTrue(result.updated_code.startswith("# Adds two values."))


class FakeGenerator:
    def generate(self, file_path, language, functions, retry_context=""):
        return {function.name: "Adds two values." for function in functions}


if __name__ == "__main__":
    unittest.main()
