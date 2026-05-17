from collections.abc import Callable
from typing import Any

import streamlit as st


def _toggle_option(state_key: str, option: Any) -> None:
    current = list(st.session_state.get(state_key, []))
    if option in current:
        st.session_state[state_key] = [x for x in current if x != option]
    else:
        st.session_state[state_key] = current + [option]


def _toggle_select_all(state_key: str, options: list[Any]) -> None:
    if len(st.session_state.get(state_key, [])) == len(options):
        st.session_state[state_key] = []
    else:
        st.session_state[state_key] = list(options)


def _option_widget_key(state_key: str, option: Any) -> str:
    return f"{state_key}__opt__{hash(option) & 0xFFFFFFFF}"


def _trigger_label(
    selected: list[Any],
    placeholder: str,
    display: Callable[[Any], str],
) -> str:
    if not selected:
        return placeholder
    labels = [display(item) for item in selected]
    if len(labels) <= 2:
        return ", ".join(labels)
    return f"{labels[0]} 외 {len(labels) - 1}개"


def filter_multiselect(
    label: str,
    options: list[Any],
    key: str,
    placeholder: str = "선택하세요 (복수 선택 가능)",
    disabled: bool = False,
    format_func: Callable[[Any], str] | None = None,
    columns: int = 3,
) -> list[Any]:
    if key not in st.session_state:
        st.session_state[key] = []

    valid = set(options)
    st.session_state[key] = [x for x in st.session_state[key] if x in valid]
    selected: list[Any] = list(st.session_state[key])

    display = format_func or (lambda x: str(x))
    trigger_text = _trigger_label(selected, placeholder, display)

    st.markdown(
        f'<p class="filter-field-label">{label}</p>',
        unsafe_allow_html=True,
    )

    if disabled:
        st.markdown(
            f'<div class="filter-trigger filter-trigger-disabled">{placeholder}</div>',
            unsafe_allow_html=True,
        )
        st.session_state[key] = []
        return []

    wrap_class = "filter-popover-wrap has-selection" if selected else "filter-popover-wrap"
    st.markdown(f'<div class="{wrap_class}" data-filter-key="{key}">', unsafe_allow_html=True)
    with st.popover(trigger_text, use_container_width=True):
        all_selected = bool(options) and len(selected) == len(options)
        st.checkbox(
            "전체 선택",
            value=all_selected,
            key=f"{key}__select_all_{len(options)}",
            on_change=_toggle_select_all,
            args=(key, options),
        )
        st.markdown('<hr class="filter-divider">', unsafe_allow_html=True)

        if not options:
            st.caption("선택 가능한 항목이 없습니다.")
        else:
            per_row = max(columns, 1)
            for row_start in range(0, len(options), per_row):
                cols = st.columns(per_row)
                row_opts = options[row_start : row_start + per_row]
                for col, opt in zip(cols, row_opts):
                    with col:
                        st.checkbox(
                            display(opt),
                            value=opt in selected,
                            key=_option_widget_key(key, opt),
                            on_change=_toggle_option,
                            args=(key, opt),
                        )
    st.markdown("</div>", unsafe_allow_html=True)

    return list(st.session_state[key])
