from backend.agents.orchestrator import AgenticCodeReviewOrchestrator

def test_sqli_and_missing_error_handling_detected():
    sample_diff = """diff --git a/auth/login.py b/auth/login.py
--- a/auth/login.py
+++ b/auth/login.py
@@ -48,6 +48,6 @@ def login(user, pwd):
-    if user and pwd:
+    if user:
-    query = "SELECT * FROM users WHERE user = ?"
+    query = f"SELECT * FROM users WHERE user = '{user}'"
"""
    orchestrator = AgenticCodeReviewOrchestrator()
    result = orchestrator.run_review(sample_diff)
    categories = [f["category"] for f in result["findings"]]
    assert "Security Issue" in categories
    assert "Error Handling Missing" in categories
    assert result["summary"]["total_chunks_processed"] >= 1
