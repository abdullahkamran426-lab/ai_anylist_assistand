"""
Upload Dataset page styles
==========================
Everything specific to the Upload Dataset page: the drag-and-drop
st.file_uploader() dropzone re-skin, the empty state shown before a file
is picked, the success banner shown after a file loads, the small
requirement chips row ("Comma-separated", "UTF-8 or CP1252", etc.),
and the "Next up" call-to-action cards that link to Clean Data /
Statistics / AI Assistant.

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

UPLOAD_CSS = """
/* ============================================================================
   FILE UPLOADER DROPZONE
   Styling for st.file_uploader() component
============================================================================ */
[data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(180deg, rgba(99,102,241,.06) 0%, rgba(99,102,241,.02) 100%) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 16px !important;
    padding: 8px !important;
    transition: border-color .2s, background .2s;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent) !important;
    background: linear-gradient(180deg, rgba(99,102,241,.1) 0%, rgba(99,102,241,.03) 100%) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: var(--muted) !important;
}
[data-testid="stFileUploaderFile"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* ============================================================================
   UPLOAD EMPTY STATE
   Styling for the empty state when no file is uploaded
============================================================================ */
.upload-empty {
    text-align: center;
    padding: 10px 20px 4px;
}
.upload-empty .icon {
    font-size: 2.6rem;
    margin-bottom: 6px;
    filter: drop-shadow(0 6px 18px rgba(99,102,241,.35));
}
.upload-empty .title { font-weight: 700; color: #fff; font-size: 1.05rem; margin-bottom: 4px; }
.upload-empty .desc  { color: var(--muted); font-size: .87rem; max-width: 420px; margin: 0 auto; line-height: 1.6; }

/* ============================================================================
   UPLOAD SUCCESS BANNER
   Styling for the success banner after file upload
============================================================================ */
.upload-success {
    display: flex;
    align-items: center;
    gap: 16px;
    background: linear-gradient(135deg, rgba(34,211,165,.12) 0%, rgba(34,211,165,.03) 100%);
    border: 1px solid rgba(34,211,165,.35);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 22px;
}
.upload-success .check {
    width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
    background: rgba(34,211,165,.18); color: var(--success);
    display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
}
.upload-success .fname { font-weight: 700; color: #fff; font-size: .98rem; word-break: break-all; }
.upload-success .fmeta { color: var(--muted); font-size: .82rem; margin-top: 2px; }

/* ============================================================================
   REQUIREMENT CHIP ROW
   Row of requirement chips for upload page
============================================================================ */
.req-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 14px; }
.req-chip {
    display: flex; align-items: center; gap: 6px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 99px; padding: 5px 12px; font-size: .78rem; color: var(--muted);
}

/* ============================================================================
   NEXT-STEP CTA CARD
   Cards for next step suggestions
============================================================================ */
.next-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
}
.next-card .n-icon { font-size: 1.3rem; margin-bottom: 6px; }
.next-card .n-title { font-weight: 700; color: #fff; font-size: .9rem; margin-bottom: 3px; }
.next-card .n-desc { color: var(--muted); font-size: .8rem; line-height: 1.5; }
"""
