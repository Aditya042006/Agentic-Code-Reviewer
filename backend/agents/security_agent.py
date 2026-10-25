import re
from typing import List, Dict, Any
from backend.utils.retry_handler import with_agent_retry

class SecurityReviewAgent:
    """
    Stage 2 Agent: Inspects code changes for SQL Injection, hardcoded credentials,
    command injection, unsafe eval/exec, and authentication bypasses.
    """

    @with_agent_retry(max_retries=3, base_delay=0.2)
    def analyze_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        entries = chunk.get("entries", [])

        for item in entries:
            if item["type"] == "removed":
                continue

            code = item["content"]
            line_no = item["line_number"]
            file_name = item["file"]

            # 1. SQL Injection check (f-strings or string concatenation in SQL queries)
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE)\s+.*(\{.*\}|%s|\+\s*\w+)', code, re.IGNORECASE) and (
                'f"' in code or "f'" in code or "+" in code or "%" in code
            ):
                findings.append({
                    "category": "Security Issue",
                    "severity": "CRITICAL",
                    "confidence": 0.96,
                    "file": file_name,
                    "line": line_no,
                    "title": "Possible SQL Injection vulnerability",
                    "description": "Dynamic string interpolation detected inside raw SQL query statement.",
                    "suggestion": "Use parameterized queries (e.g., cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))) to prevent SQL injection."
                })

            # 2. Hardcoded API keys / secrets
            if re.search(r'(api_key|secret_key|password|passwd|access_token)\s*=\s*["'][A-Za-z0-9_\-]{8,}["']', code, re.IGNORECASE):
                findings.append({
                    "category": "Security Issue",
                    "severity": "HIGH",
                    "confidence": 0.92,
                    "file": file_name,
                    "line": line_no,
                    "title": "Hardcoded Credential / Secret Exposed",
                    "description": "Sensitive secret or credential assigned directly as a string literal in source code.",
                    "suggestion": "Load secrets securely from environment variables using os.getenv() or a secrets manager."
                })

            # 3. Unsafe command execution / eval
            if re.search(r'(eval|exec)\s*\(|subprocess\.(Popen|call|run)\(.*shell\s*=\s*True', code):
                findings.append({
                    "category": "Security Issue",
                    "severity": "HIGH",
                    "confidence": 0.90,
                    "file": file_name,
                    "line": line_no,
                    "title": "Unsafe Code / Shell Execution",
                    "description": "Use of eval(), exec(), or subprocess with shell=True enables arbitrary command injection.",
                    "suggestion": "Avoid eval/exec on untrusted input; pass command arguments as a list with shell=False."
                })

        # Check removed lines vs added lines for weakened auth checks
        removed_lines = [e for e in entries if e["type"] == "removed"]
        added_lines = [e for e in entries if e["type"] == "added"]
        for rem in removed_lines:
            if re.search(r'if\s+.*and\s+(pwd|password|token|auth)', rem["content"]):
                for add in added_lines:
                    if re.search(r'if\s+\w+\s*:', add["content"]) and "pwd" not in add["content"] and "password" not in add["content"]:
                        findings.append({
                            "category": "Security Issue",
                            "severity": "CRITICAL",
                            "confidence": 0.94,
                            "file": add["file"],
                            "line": add["line_number"],
                            "title": "Authentication Validation Weakened",
                            "description": "Password/credential verification condition was removed from authentication check.",
                            "suggestion": "Restore explicit credential verification and hash comparison (e.g., hmac.compare_digest)."
                        })

        return findings
