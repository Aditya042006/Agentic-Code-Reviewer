import re
from typing import List, Dict, Any
from backend.utils.retry_handler import with_agent_retry

class QualityAndTestingAgent:
    """
    Stage 3 Agent: Detects missing error handling (try/except), unchecked external IO/DB calls,
    resource leaks, and missing unit test coverage.
    """

    @with_agent_retry(max_retries=3, base_delay=0.2)
    def analyze_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        entries = [e for e in chunk.get("entries", []) if e["type"] != "removed"]

        full_chunk_text = "\n".join(e["content"] for e in entries)
        has_try_block = "try:" in full_chunk_text

        for item in entries:
            code = item["content"]
            line_no = item["line_number"]
            file_name = item["file"]

            # 1. Missing error handling around DB / network / file operations
            if re.search(r'(SELECT|INSERT|UPDATE|cursor\.execute|requests\.(get|post|put|delete)|session\.query)', code, re.IGNORECASE):
                if not has_try_block:
                    findings.append({
                        "category": "Error Handling Missing",
                        "severity": "MEDIUM",
                        "confidence": 0.88,
                        "file": file_name,
                        "line": line_no,
                        "title": "No Exception Handling for External/DB Operation",
                        "description": "Database query or external network call is executed without a try-except block.",
                        "suggestion": "Wrap the database/network call in a try-except block, log the error context, and raise or return a safe fallback."
                    })

            # 2. Bare except clause
            if re.search(r'^\s*except\s*:\s*$', code):
                findings.append({
                    "category": "Error Handling Missing",
                    "severity": "MEDIUM",
                    "confidence": 0.85,
                    "file": file_name,
                    "line": line_no,
                    "title": "Bare 'except:' Clause Swallows System Exceptions",
                    "description": "Catching bare except hides KeyboardInterrupt, SystemExit, and unexpected bugs.",
                    "suggestion": "Catch specific exception types (e.g., except (ValueError, DatabaseError) as exc:)."
                })

            # 3. Function definition without corresponding unit test in diff
            func_match = re.search(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            if func_match:
                func_name = func_match.group(1)
                if not func_name.startswith("test_") and f"test_{func_name}" not in full_chunk_text:
                    findings.append({
                        "category": "Test Missing",
                        "severity": "LOW",
                        "confidence": 0.82,
                        "file": file_name,
                        "line": line_no,
                        "title": f"Missing Unit Tests for '{func_name}()'",
                        "description": f"No unit test coverage detected for modified function '{func_name}' and its edge-case logic.",
                        "suggestion": f"Add unit tests covering valid inputs, invalid credentials/inputs, and database failure states for '{func_name}()'."
                    })

        return findings
