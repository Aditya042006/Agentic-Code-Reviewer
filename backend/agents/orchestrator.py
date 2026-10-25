import time
from typing import Dict, Any, List
from backend.utils.chunker import DiffChunker
from backend.agents.security_agent import SecurityReviewAgent
from backend.agents.quality_agent import QualityAndTestingAgent

class AgenticCodeReviewOrchestrator:
    """
    Coordinates the 4-stage multi-agent review pipeline:
      1. Diff Understanding & Context-Safe Chunking
      2. Security Vulnerability Analysis
      3. Error Handling & Unit Test Verification
      4. Critic Filtering (False-Positive Suppression) & Final Structured Review
    """

    def __init__(self, max_chars_per_chunk: int = 3500, confidence_threshold: float = 0.78):
        self.chunker = DiffChunker(max_chars_per_chunk=max_chars_per_chunk)
        self.security_agent = SecurityReviewAgent()
        self.quality_agent = QualityAndTestingAgent()
        self.confidence_threshold = confidence_threshold

    def run_review(self, raw_diff: str) -> Dict[str, Any]:
        start_time = time.time()

        # Step 1: Parse & Chunk Diff (prevents ContextWindowExceededError)
        chunks = self.chunker.parse_and_chunk(raw_diff)
        raw_candidates: List[Dict[str, Any]] = []
        step_logs: List[Dict[str, Any]] = []

        step_logs.append({
            "step": "1. Understand Changes & Context Chunking",
            "status": "SUCCESS",
            "details": f"Parsed diff into {len(chunks)} token-safe chunk(s)."
        })

        # Step 2 & 3: Execute Specialized Agents per Chunk with Retry Protection
        security_count = 0
        quality_count = 0
        for chunk in chunks:
            sec_findings = self.security_agent.analyze_chunk(chunk)
            qual_findings = self.quality_agent.analyze_chunk(chunk)
            security_count += len(sec_findings)
            quality_count += len(qual_findings)
            raw_candidates.extend(sec_findings)
            raw_candidates.extend(qual_findings)

        step_logs.append({
            "step": "2. Security Vulnerability Agent",
            "status": "SUCCESS",
            "details": f"Scanned {len(chunks)} chunk(s); flagged {security_count} potential security issue(s)."
        })
        step_logs.append({
            "step": "3. Error Handling & Test Coverage Agent",
            "status": "SUCCESS",
            "details": f"Identified {quality_count} error-handling / unit-test gap(s)."
        })

        # Step 4: Critic Agent - Suppress False Alarms & Deduplicate
        accepted_findings, suppressed_count = self._critic_filter(raw_candidates)

        step_logs.append({
            "step": "4. Final Critic & False-Alarm Filter",
            "status": "SUCCESS",
            "details": f"Retained {len(accepted_findings)} high-confidence finding(s); suppressed {suppressed_count} low-confidence false alarm(s)."
        })

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "summary": {
                "total_chunks_processed": len(chunks),
                "total_issues_found": len(accepted_findings),
                "false_alarms_suppressed": suppressed_count,
                "execution_time_ms": elapsed_ms,
                "risk_level": self._compute_overall_risk(accepted_findings),
            },
            "agent_trace": step_logs,
            "findings": accepted_findings,
        }

    def _critic_filter(self, candidates: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
        accepted: List[Dict[str, Any]] = []
        seen_keys = set()
        suppressed = 0

        for item in candidates:
            if item.get("confidence", 0.0) < self.confidence_threshold:
                suppressed += 1
                continue
            dedup_key = (item["file"], item["line"], item["title"])
            if dedup_key in seen_keys:
                suppressed += 1
                continue
            seen_keys.add(dedup_key)
            accepted.append(item)

        # Sort by severity priority
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        accepted.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["line"]))
        return accepted, suppressed

    @staticmethod
    def _compute_overall_risk(findings: List[Dict[str, Any]]) -> str:
        severities = {f["severity"] for f in findings}
        if "CRITICAL" in severities:
            return "CRITICAL (Block Merge)"
        if "HIGH" in severities:
            return "HIGH (Changes Requested)"
        if "MEDIUM" in severities:
            return "MODERATE (Review Recommended)"
        return "LOW (Safe to Merge)"
