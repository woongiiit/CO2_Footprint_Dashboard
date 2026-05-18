import streamlit as st


def period_range_select(
    label: str,
    period_options: list[tuple[str, str]],
    key_prefix: str = "filter_period_range",
) -> tuple[str | None, str | None]:
    """기간 구간의 시작·종료 월을 선택한다. (period_key, label) 목록을 받는다."""
    keys = [p[0] for p in period_options]
    labels = {p[0]: p[1] for p in period_options}
    start_key = f"{key_prefix}_start"
    end_key = f"{key_prefix}_end"

    st.markdown(f'<p class="filter-field-label">{label}</p>', unsafe_allow_html=True)
    col_start, col_sep, col_end = st.columns([5, 1, 5])
    with col_start:
        start = st.selectbox(
            "시작",
            options=keys,
            format_func=lambda k: labels.get(k, k),
            index=None,
            placeholder="시작 월",
            key=start_key,
            label_visibility="collapsed",
        )
    with col_sep:
        st.markdown(
            '<p style="text-align:center;margin:0.65rem 0 0;color:#5c5f6a;">~</p>',
            unsafe_allow_html=True,
        )
    with col_end:
        end = st.selectbox(
            "종료",
            options=keys,
            format_func=lambda k: labels.get(k, k),
            index=None,
            placeholder="종료 월",
            key=end_key,
            label_visibility="collapsed",
        )
    return start, end
