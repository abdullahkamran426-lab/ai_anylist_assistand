"""
AI Assistant page
=================
Natural-language Q&A about the loaded dataset with richer context and
conversation history for the export report and follow-up questions.
"""

import streamlit as st

from modules.ai_helper import ask_ai
from modules.analysis import get_summary


def render_ai_assistant_page():
    df = st.session_state.df

    if df is None:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:2px solid #22d3a5;border-radius:12px;padding:20px 24px;margin:20px 0'>
            <div style='display:flex;align-items:center;gap:12px'>
                <div style='font-size:1.5rem'>📂</div>
                <div>
                    <div style='font-weight:700;color:#fff;font-size:1rem'>Upload a dataset first</div>
                    <div style='color:#94a3b8;font-size:.87rem;margin-top:2px'>
                        Go to the Upload Dataset page to get started.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "ai_prefill" not in st.session_state:
        st.session_state.ai_prefill = ""

    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1d27 0%,#241a3d 55%,#1a1d27 100%);
                border:1px solid var(--border);border-radius:18px;
                padding:32px 36px;margin-bottom:24px;position:relative;overflow:hidden'>
        <div style='position:absolute;top:-60px;right:-40px;width:220px;height:220px;
                    background:radial-gradient(circle,rgba(99,102,241,.25) 0%,transparent 70%);
                    border-radius:50%'></div>
        <div style='display:flex;align-items:center;gap:16px;position:relative'>
            <div style='width:52px;height:52px;border-radius:14px;
                        background:linear-gradient(135deg,#6366f1,#818cf8);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.6rem;flex-shrink:0;
                        box-shadow:0 8px 24px rgba(99,102,241,.35)'>🤖</div>
            <div>
                <div style='font-family:Space Grotesk;font-size:1.4rem;font-weight:700;color:#fff;margin-bottom:2px'>Ask your data anything</div>
                <div style='color:#94a3b8;font-size:.88rem'>Context-aware analysis, visualization ideas, and dataset summaries are generated automatically.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nums = df.select_dtypes(include="number").columns.tolist()
    suggestions = [
        "📉 Which columns have the most missing values?",
        "📈 Summarize the key trends in this dataset",
        f"🔢 What is notable about the '{nums[0]}' column?" if nums else "🧭 What should I explore first?",
        "🧩 Are there any outliers I should worry about?",
        "📊 Which visualizations would be most useful here?",
    ]
    st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>Try asking</div>", unsafe_allow_html=True)
    chip_cols = st.columns(len(suggestions))
    for col, sug in zip(chip_cols, suggestions):
        with col:
            if st.button(sug, key=f"chip_{sug}"):
                st.session_state.ai_prefill = sug.split(" ", 1)[1]

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    if st.session_state.chat_history:
        st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px'>Conversation</div>", unsafe_allow_html=True)
        for turn in st.session_state.chat_history:
            st.markdown(f"""
            <div style='display:flex;justify-content:flex-end;margin-bottom:10px'>
                <div style='max-width:75%;background:var(--accent);color:#fff;padding:12px 16px;border-radius:16px 16px 4px 16px;font-size:.9rem;line-height:1.55'>
                    {turn['q']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style='display:flex;justify-content:flex-start;gap:10px;margin-bottom:22px'>
                <div style='width:30px;height:30px;border-radius:9px;flex-shrink:0;background:linear-gradient(135deg,#6366f1,#818cf8);display:flex;align-items:center;justify-content:center;font-size:.9rem'>🤖</div>
                <div style='max-width:75%;background:var(--card);border:1px solid var(--border);color:var(--text);padding:14px 18px;border-radius:4px 16px 16px 16px;font-size:.9rem;line-height:1.7'>
                    {turn['a']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑️ Clear conversation", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.answer = None
            st.rerun()
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#64748b;font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px'>Ask a question</div>", unsafe_allow_html=True)
    with st.form(key="ai_form", clear_on_submit=True):
        q = st.text_area(
            "Your question",
            value=st.session_state.ai_prefill,
            placeholder="e.g. Which column has the most missing values?",
            height=90,
            label_visibility="collapsed",
        )
        c1, c2 = st.columns([5, 1])
        with c2:
            submitted = st.form_submit_button("Ask AI →")

    if submitted:
        st.session_state.ai_prefill = ""
        if q.strip():
            with st.spinner("Thinking…"):
                summary = get_summary(df, st.session_state.filename)
                ans = ask_ai(q, summary)
            st.session_state.answer = ans
            st.session_state.chat_history.append({"q": q.strip(), "a": ans})
            st.rerun()
        else:
            st.warning("Please enter a question.")
