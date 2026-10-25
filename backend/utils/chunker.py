import re
from typing import List, Dict, Any

class DiffChunker:
    """
    Splits large unified git diffs into context-window-safe chunks while preserving
    file headers and exact line number mappings. Prevents ContextWindowExceeded errors.
    """
    def __init__(self, max_chars_per_chunk: int = 3500):
        self.max_chars_per_chunk = max_chars_per_chunk

    def parse_and_chunk(self, raw_diff: str) -> List[Dict[str, Any]]:
        if not raw_diff or not raw_diff.strip():
            return []

        lines = raw_diff.splitlines()
        chunks: List[Dict[str, Any]] = []
        current_file = "snippet.py"
        current_line_num = 1
        current_chunk_lines: List[Dict[str, Any]] = []
        current_char_count = 0

        hunk_header_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for raw_line in lines:
            if raw_line.startswith("+++ b/"):
                current_file = raw_line[6:].strip()
                continue
            elif raw_line.startswith("--- a/") or raw_line.startswith("diff --git"):
                continue

            hunk_match = hunk_header_re.match(raw_line)
            if hunk_match:
                current_line_num = int(hunk_match.group(1))
                continue

            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                entry = {
                    "file": current_file,
                    "line_number": current_line_num,
                    "type": "added",
                    "content": raw_line[1:],
                }
                current_line_num += 1
            elif raw_line.startswith("-") and not raw_line.startswith("---"):
                entry = {
                    "file": current_file,
                    "line_number": current_line_num,
                    "type": "removed",
                    "content": raw_line[1:],
                }
            else:
                content = raw_line[1:] if raw_line.startswith(" ") else raw_line
                entry = {
                    "file": current_file,
                    "line_number": current_line_num,
                    "type": "context",
                    "content": content,
                }
                current_line_num += 1

            current_chunk_lines.append(entry)
            current_char_count += len(raw_line)

            if current_char_count >= self.max_chars_per_chunk:
                chunks.append({
                    "chunk_id": len(chunks) + 1,
                    "file": current_file,
                    "entries": current_chunk_lines,
                    "char_size": current_char_count,
                })
                current_chunk_lines = []
                current_char_count = 0

        if current_chunk_lines:
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "file": current_file,
                "entries": current_chunk_lines,
                "char_size": current_char_count,
            })

        return chunks
