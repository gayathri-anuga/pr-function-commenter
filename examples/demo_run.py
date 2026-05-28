import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pr_function_commenter.diff import changed_lines_from_patch
from src.pr_function_commenter.extractor import extract_changed_functions
from src.pr_function_commenter.languages import language_for_path
from src.pr_function_commenter.llm import StaticCommentGenerator
from src.pr_function_commenter.workflow import generate_validated_file


code = """def calculate_refund_amount(order, previous_refunds):
    paid = sum(item["price"] for item in order["items"])
    refundable = paid - previous_refunds
    return max(0, refundable)
"""

patch = """@@ -0,0 +1,4 @@
+def calculate_refund_amount(order, previous_refunds):
+    paid = sum(item["price"] for item in order["items"])
+    refundable = paid - previous_refunds
+    return max(0, refundable)
"""

language = language_for_path("refunds.py")
functions = extract_changed_functions(code, changed_lines_from_patch(patch), language)
result = generate_validated_file(
    file_path="refunds.py",
    original_code=code,
    functions=functions,
    language=language,
    comment_generator=StaticCommentGenerator(),
    max_attempts=3,
)

print(result.updated_code)
