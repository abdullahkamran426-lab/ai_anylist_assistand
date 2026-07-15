"""
Clean Data page
===============
The interactive cleaning pipeline: duplicate removal, missing-value
strategies, drop/rename columns, dtype casting, row filtering, a
live preview, and a running audit log. Every control mutates `df`,
saves it back to st.session_state, appends a message to clean_log,
then calls st.rerun() to redraw the page with the updated data.
"""

import pandas as pd
import streamlit as st

from modules.analysis import apply_one_hot_encoding, apply_label_encoding, get_encoding_recommendations
from modules.utils import section


def render_clean_data_page():
    """
    Render the Clean Data page.
    Interactive cleaning pipeline with live preview and audit log.
    Every control mutates df, saves it back to session_state, appends to clean_log,
    then calls st.rerun() to redraw with updated data.
    """
    df = st.session_state.df

    # Guard: this page is meaningless without data
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

    section("DATA CLEANING", "Fix, reshape & prepare")

    # ------------------------------------------------------------------------
    # BEFORE/AFTER KPIs
    # Compare current state against original upload
    # ------------------------------------------------------------------------
    orig = st.session_state.original_df
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Current rows",    f"{df.shape[0]:,}",  f"{df.shape[0]-orig.shape[0]:,}" if orig is not None else None)
    col_b.metric("Missing cells",   int(df.isna().sum().sum()),
                 f"{int(df.isna().sum().sum()) - int(orig.isna().sum().sum())}" if orig is not None else None)
    col_c.metric("Duplicate rows",  int(df.duplicated().sum()))
    col_d.metric("Columns",         df.shape[1])

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # DOWNLOAD CLEANED DATASET
    # Encode current dataframe to CSV for download buttons
    # ------------------------------------------------------------------------
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    clean_filename = f"cleaned_{st.session_state.filename or 'dataset.csv'}"
    if not clean_filename.lower().endswith(".csv"):
        clean_filename += ".csv"

    dl_col1, dl_col2 = st.columns([3, 1])
    with dl_col1:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,rgba(34,211,165,.12) 0%,rgba(34,211,165,.03) 100%);
                    border:1px solid rgba(34,211,165,.35);border-radius:var(--radius);
                    padding:16px 20px;display:flex;align-items:center;gap:14px;height:100%'>
            <div style='width:38px;height:38px;border-radius:10px;flex-shrink:0;
                        background:rgba(34,211,165,.18);color:var(--success);
                        display:flex;align-items:center;justify-content:center;font-size:1.1rem'>⬇️</div>
            <div>
                <div style='color:#fff;font-weight:700;font-size:.9rem'>Cleaned dataset ready</div>
                <div style='color:#94a3b8;font-size:.8rem'>
                    {df.shape[0]:,} rows · {df.shape[1]} columns · {len(st.session_state.clean_log)} step(s) applied
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with dl_col2:
        st.markdown("<div style='height:100%;display:flex;align-items:center'>", unsafe_allow_html=True)
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=clean_filename,
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # TWO-COLUMN LAYOUT
    # Left: cleaning controls, Right: live preview
    # ------------------------------------------------------------------------
    ctrl, prev = st.columns([1, 1.6], gap="large")

    with ctrl:
        # --------------------------------------------------------------------
        # 1. DUPLICATE ROWS
        # Detect and remove exact row-level duplicates
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>🔂 Duplicate Rows</h4>", unsafe_allow_html=True)
        dup_count = int(df.duplicated().sum())
        st.markdown(f"<span class='pill pill-{'red' if dup_count else 'green'}'>"
                    f"{'⚠️ ' if dup_count else '✅ '}{dup_count} duplicate{'s' if dup_count!=1 else ''}</span>",
                    unsafe_allow_html=True)
        if dup_count and st.button("Remove duplicates", key="rm_dup"):
            df = df.drop_duplicates().reset_index(drop=True)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Removed {dup_count} duplicate rows")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 2. MISSING VALUES
        # Per-column strategy picker (drop / mean / median / mode / constant)
        # --------------------------------------------------------------------
        missing_cols = df.columns[df.isna().any()].tolist()
        st.markdown("<div class='clean-panel'><h4>❓ Missing Values</h4>", unsafe_allow_html=True)
        if not missing_cols:
            st.markdown("<span class='pill pill-green'>✅ No missing values</span>", unsafe_allow_html=True)
        else:
            # Show one pill per affected column
            for col in missing_cols:
                cnt = int(df[col].isna().sum())
                pct = cnt / len(df) * 100
                st.markdown(f"<span class='pill pill-yellow'>⚠️ {col}: {cnt} ({pct:.1f}%)</span>",
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            mv_col   = st.selectbox("Column", missing_cols, key="mv_col")
            mv_strat = st.selectbox("Strategy", ["Drop rows", "Fill with mean",
                                                  "Fill with median", "Fill with mode",
                                                  "Fill with constant"], key="mv_strat")
            mv_const = ""
            if mv_strat == "Fill with constant":
                mv_const = st.text_input("Constant value", key="mv_const")

            if st.button("Apply", key="apply_mv"):
                col_data = df[mv_col]
                before   = int(col_data.isna().sum())
                
                # Apply selected strategy
                if mv_strat == "Drop rows":
                    df = df.dropna(subset=[mv_col]).reset_index(drop=True)
                    msg = f"✅ Dropped {before} rows with nulls in '{mv_col}'"
                elif mv_strat == "Fill with mean" and pd.api.types.is_numeric_dtype(col_data):
                    df[mv_col] = col_data.fillna(col_data.mean())
                    msg = f"✅ Filled '{mv_col}' nulls with mean ({col_data.mean():.4g})"
                elif mv_strat == "Fill with median" and pd.api.types.is_numeric_dtype(col_data):
                    df[mv_col] = col_data.fillna(col_data.median())
                    msg = f"✅ Filled '{mv_col}' nulls with median ({col_data.median():.4g})"
                elif mv_strat == "Fill with mode":
                    mode_val = col_data.mode()[0]
                    df[mv_col] = col_data.fillna(mode_val)
                    msg = f"✅ Filled '{mv_col}' nulls with mode ({mode_val})"
                elif mv_strat == "Fill with constant" and mv_const != "":
                    try:
                        fill = float(mv_const) if pd.api.types.is_numeric_dtype(col_data) else mv_const
                    except ValueError:
                        fill = mv_const
                    df[mv_col] = col_data.fillna(fill)
                    msg = f"✅ Filled '{mv_col}' nulls with '{fill}'"
                else:
                    msg = "⚠️ Strategy not applicable to column type — skipped."
                
                st.session_state.df = df
                st.session_state.clean_log.append(msg)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 3. DROP COLUMNS
        # Remove one or more columns entirely
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>🗑️ Drop Columns</h4>", unsafe_allow_html=True)
        drop_cols = st.multiselect("Select columns to drop", df.columns.tolist(), key="drop_cols")
        if drop_cols and st.button("Drop selected", key="apply_drop"):
            df = df.drop(columns=drop_cols)
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Dropped columns: {', '.join(drop_cols)}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 4. RENAME COLUMN
        # Simple find/replace on a single column header
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>✏️ Rename Column</h4>", unsafe_allow_html=True)
        ren_from = st.selectbox("Column to rename", df.columns.tolist(), key="ren_from")
        ren_to   = st.text_input("New name", key="ren_to")
        if st.button("Rename", key="apply_rename") and ren_to:
            df = df.rename(columns={ren_from: ren_to})
            st.session_state.df = df
            st.session_state.clean_log.append(f"✅ Renamed '{ren_from}' → '{ren_to}'")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 5. CAST DTYPE
        # Force a column to int/float/str/datetime
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>🔁 Change Column Type</h4>", unsafe_allow_html=True)
        cast_col   = st.selectbox("Column", df.columns.tolist(), key="cast_col")
        cast_dtype = st.selectbox("Target type", ["int", "float", "str", "datetime"], key="cast_dtype")
        if st.button("Cast", key="apply_cast"):
            try:
                if cast_dtype == "datetime":
                    df[cast_col] = pd.to_datetime(df[cast_col], errors="coerce")
                else:
                    df[cast_col] = df[cast_col].astype(cast_dtype)
                st.session_state.df = df
                st.session_state.clean_log.append(f"✅ Cast '{cast_col}' to {cast_dtype}")
            except Exception as exc:
                st.error(f"Could not cast: {exc}")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 6. FILTER ROWS
        # Keep only rows matching a simple numeric comparison
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>🔍 Filter Rows</h4>", unsafe_allow_html=True)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            flt_col = st.selectbox("Numeric column", num_cols, key="flt_col")
            flt_op  = st.selectbox("Operator", [">", ">=", "<", "<=", "==", "!="], key="flt_op")
            flt_val = st.number_input("Value", key="flt_val")
            if st.button("Apply filter", key="apply_flt"):
                before = len(df)
                expr   = f"`{flt_col}` {flt_op} {flt_val}"
                df     = df.query(expr).reset_index(drop=True)
                st.session_state.df = df
                st.session_state.clean_log.append(
                    f"✅ Filter '{flt_col} {flt_op} {flt_val}' kept {len(df):,}/{before:,} rows")
                st.rerun()
        else:
            st.caption("No numeric columns available.")
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 7. ENCODING
        # One-hot encoding and label encoding for categorical columns
        # --------------------------------------------------------------------
        st.markdown("<div class='clean-panel'><h4>Encoding</h4>", unsafe_allow_html=True)
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if not cat_cols:
            st.markdown("<span class='pill pill-green'>No categorical columns</span>", unsafe_allow_html=True)
        else:
            # Show encoding recommendations
            st.markdown("<small style='color:#94a3b8'>Encoding recommendations:</small>", unsafe_allow_html=True)
            recommendations = get_encoding_recommendations(df)
            for col, rec in recommendations.items():
                st.markdown(f"<span class='pill pill-blue'>{col}: {rec['recommended_encoding']}</span>",
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            enc_col = st.multiselect("Select columns to encode", cat_cols, key="enc_cols")
            enc_type = st.selectbox("Encoding type", ["One-Hot Encoding", "Label Encoding"], key="enc_type")
            
            if enc_type == "One-Hot Encoding":
                drop_first = st.checkbox("Drop first category (avoid multicollinearity)", key="drop_first")
            else:
                drop_first = False
            
            if st.button("Apply encoding", key="apply_enc"):
                if enc_col:
                    try:
                        if enc_type == "One-Hot Encoding":
                            df = apply_one_hot_encoding(df, columns=enc_col, drop_first=drop_first)
                            msg = f"Applied one-hot encoding to: {', '.join(enc_col)}"
                        else:
                            df, encoders = apply_label_encoding(df, columns=enc_col)
                            msg = f"Applied label encoding to: {', '.join(enc_col)}"
                        
                        st.session_state.df = df
                        st.session_state.clean_log.append(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Encoding failed: {str(e)}")
                else:
                    st.warning("Please select at least one column to encode.")
        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # 8. RESET & DOWNLOAD
        # Undo everything back to original, or download current state
        # --------------------------------------------------------------------
        st.markdown("<div class='div'></div>", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("Reset to original", key="reset_clean"):
                st.session_state.df = st.session_state.original_df.copy()
                st.session_state.clean_log = ["↩️ Reset to original dataset"]
                st.rerun()
        with rc2:
            st.download_button(
                "⬇️ Download CSV",
                data=csv_bytes,
                file_name=clean_filename,
                mime="text/csv",
                key="dl_csv_bottom",
            )

    with prev:
        # --------------------------------------------------------------------
        # LIVE PREVIEW
        # Right-hand column always reflects current df state
        # --------------------------------------------------------------------
        st.markdown("#### Live Preview")
        st.dataframe(df.head(50), height=340)

        # Missing-value heatmap summary
        if df.isna().any().any():
            st.markdown("#### Missing-value breakdown")
            miss = (df.isna().sum()
                      .rename("Missing")
                      .to_frame()
                      .assign(Pct=lambda d: (d["Missing"]/len(df)*100).round(2))
                      .query("Missing > 0"))
            st.dataframe(miss)

        # Clean log - running audit trail
        if st.session_state.clean_log:
            st.markdown("#### Cleaning log")
            for entry in reversed(st.session_state.clean_log):
                st.markdown(f"<small style='color:#94a3b8'>{entry}</small>", unsafe_allow_html=True)
