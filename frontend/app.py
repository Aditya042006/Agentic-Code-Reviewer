import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend.agents.orchestrator import AgenticCodeReviewOrchestrator
from benchmarks.evaluate_historical_bugs import run_benchmark

st.set_page_config(
    page_title="Agentic Code Reviewer",
    page_icon="🛡️",
    layout="wide",
)

# Custom Dark Developer UI Styling
st.markdown("""
<style>
    .issue-card {
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: #161b22;
        border-left: 6px solid #30363d;
        color: #e6edf3;
    }
    .sev-CRITICAL { border-left-color: #ff4b4b; }
    .sev-HIGH { border-left-color: #ff9100; }
    .sev-MEDIUM { border-left-color: #faca2b; }
    .sev-LOW { border-left-color: #3fb950; }
    .line-badge {
        float: right;
        background: #21262d;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.88rem;
        color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Agentic Code Reviewer")
st.caption("Multi-Step AI Code Review Pipeline • Security & Error Handling • Context-Window Chunking • Real-World Bug Benchmark")

DEFAULT_SAMPLE_DIFF = """diff --git a/auth/login.py b/auth/login.py
index 1029384..8971234 100644
--- a/auth/login.py
+++ b/auth/login.py
@@ -48,9 +48,9 @@ def login(user, pwd):
-    if user and pwd:
+    if user:
         
-    query = "SELECT * FROM users WHERE username = ?"
+    query = f"SELECT * FROM users WHERE username = '{user}'"
     db.execute(query)
     return True
"""

with st.sidebar:
    st.header("⚙️ Agent Configuration")
    max_chunk_chars = st.slider("Max Context Chunk Size (Chars)", 500, 10000, 3500, step=500)
    confidence_threshold = st.slider("Critic Confidence Threshold", 0.50, 0.95, 0.78, step=0.02)
    st.markdown("---")
    st.markdown("**Multi-Step Workflow:**")
    st.markdown("1. `DiffChunker`: Prevents context overflow\n2. `SecurityAgent`: SQLi, Auth & Secrets\n3. `QualityAgent`: Error Handling & Tests\n4. `CriticAgent`: Filters False Alarms")

tab1, tab2 = st.tabs(["🔍 Interactive PR / Diff Review", "📊 Real-World Bug Benchmark"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Code Changes (Git Diff Input)")
        diff_input = st.text_area("Paste unified `git diff` or PR patch:", value=DEFAULT_SAMPLE_DIFF, height=340)
        run_btn = st.button("🚀 Run Multi-Step Agentic Review", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. Structured Agent Review")
        if run_btn:
            orchestrator = AgenticCodeReviewOrchestrator(
                max_chars_per_chunk=max_chunk_chars,
                confidence_threshold=confidence_threshold,
            )
            result = orchestrator.run_review(diff_input)
            summary = result["summary"]

            m1, m2, m3 = st.columns(3)
            m1.metric("Issues Flagged", summary["total_issues_found"])
            m2.metric("Chunks Processed", summary["total_chunks_processed"])
            m3.metric("Latency (ms)", f"{summary['execution_time_ms']} ms")

            st.info(f"**Merge Recommendation:** `{summary['risk_level']}`")

            for finding in result["findings"]:
                st.markdown(f"""
                <div class="issue-card sev-{finding['severity']}">
                    <span class="line-badge">{finding['file']} • Line {finding['line']}</span>
                    <strong>[{finding['severity']}] {finding['category']}: {finding['title']}</strong>
                    <p style="margin: 6px 0; font-size: 0.92rem;">{finding['description']}</p>
                    <div style="background:#0d1117; padding:8px 12px; border-radius:6px; font-size:0.86rem; color:#7ee787;">
                        💡 <strong>Suggestion:</strong> {finding['suggestion']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("🧭 View Multi-Step Agent Execution Trace"):
                st.json(result["agent_trace"])

with tab2:
    st.subheader("Evaluate Reviewer on Historical Bug Commits")
    st.write("Tests the agentic pipeline on historical buggy commits to measure **Actual Bugs Caught** vs **False Alarms Raised**.")
    if st.button("▶️ Run Historical Benchmark Suite"):
        metrics = run_benchmark()
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Actual Bugs Caught", metrics["actual_bugs_caught"])
        b2.metric("False Alarms Raised", metrics["false_alarms_raised"])
        b3.metric("Precision", f"{metrics['precision_pct']}%")
        b4.metric("Recall", f"{metrics['recall_pct']}%")
        st.dataframe(metrics["commit_results"], use_container_width=True)
