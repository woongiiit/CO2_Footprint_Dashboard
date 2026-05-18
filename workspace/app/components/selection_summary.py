import html

import streamlit as st

from services.data_service import get_daebunryu_options, get_province_options


def format_sigungu_label(full_name: str, province_count: int) -> str:
    if province_count == 1 and " " in full_name:
        return full_name.split(" ", 1)[1]
    return full_name


def _compact_list_summary(
    items: list[str],
    *,
    empty_label: str = "전체",
    max_shown: int = 2,
    all_count: int | None = None,
    label_fn=None,
) -> str:
    if not items:
        return empty_label
    if all_count is not None and len(items) >= all_count:
        return f"전체 ({all_count}개)"
    labels = [label_fn(item) if label_fn else item for item in items]
    if len(labels) <= max_shown:
        return ", ".join(labels)
    return f"{labels[0]} 외 {len(labels) - 1}개"


def _wrap_summary_value(text: str, max_line_chars: int = 16) -> str:
    """쉼표·공백 단위로 끊어 단어 중간 개행을 방지."""
    if not text or len(text) <= max_line_chars:
        return text

    if " 외 " in text:
        head, tail = text.rsplit(" 외 ", 1)
        head_lines = _wrap_summary_value(head.strip(), max_line_chars)
        return f"{head_lines}\n외 {tail}"

    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) > 1:
        lines: list[str] = []
        current = ""
        for part in parts:
            candidate = part if not current else f"{current}, {part}"
            if len(candidate) <= max_line_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = part
        if current:
            lines.append(current)
        return "\n".join(lines)

    tokens = text.split()
    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = token if not current else f"{current} {token}"
        if len(candidate) <= max_line_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = token
    if current:
        lines.append(current)
    return "\n".join(lines) if lines else text


def _compact_sections(
    provinces, sigungu, daebunryu, jungbunryu, period_summary
) -> list[tuple[str, str]]:
    province_total = len(get_province_options())
    prov = _compact_list_summary(
        provinces, all_count=province_total, max_shown=2
    )
    if sigungu:
        sig = _compact_list_summary(
            sigungu,
            max_shown=2,
            label_fn=lambda s: format_sigungu_label(s, len(provinces)),
        )
    elif provinces:
        sig = "선택 도 전체"
    else:
        sig = "전체"
    dae_total = len(get_daebunryu_options())
    dae = _compact_list_summary(daebunryu, all_count=dae_total, max_shown=2)
    if jungbunryu:
        jung = _compact_list_summary(jungbunryu, max_shown=2)
    elif daebunryu:
        jung = "선택 대분류 전체"
    else:
        jung = "전체"
    return [
        ("도", prov),
        ("시군구", sig),
        ("업종(대분류)", dae),
        ("업종(중분류)", jung),
        ("기간", period_summary),
    ]


def _full_sections(
    provinces, sigungu, daebunryu, jungbunryu, period_summary
) -> list[tuple[str, str]]:
    prov = ", ".join(provinces) if provinces else "전체"
    if sigungu:
        sig = ", ".join(
            format_sigungu_label(s, len(provinces)) for s in sigungu
        )
    elif provinces:
        sig = "선택 도 전체"
    else:
        sig = "전체"
    dae = ", ".join(daebunryu) if daebunryu else "전체"
    if jungbunryu:
        jung = ", ".join(jungbunryu)
    elif daebunryu:
        jung = "선택 대분류 전체"
    else:
        jung = "전체"
    return [
        ("도", prov),
        ("시군구", sig),
        ("업종(대분류)", dae),
        ("업종(중분류)", jung),
        ("기간", period_summary),
    ]


def _render_vertical_summary(sections: list[tuple[str, str]]) -> None:
    blocks = []
    for label, value in sections:
        wrapped = _wrap_summary_value(value)
        safe_label = html.escape(label)
        safe_value = html.escape(wrapped).replace("\n", "<br>")
        blocks.append(
            f'<div class="summary-v-item">'
            f'<div class="summary-v-label">{safe_label}</div>'
            f'<div class="summary-v-value">{safe_value}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="summary-v-box">{"".join(blocks)}</div>',
        unsafe_allow_html=True,
    )


def _render_expanded_detail(sections: list[tuple[str, str]]) -> None:
    for label, value in sections:
        wrapped = _wrap_summary_value(value, max_line_chars=28)
        st.markdown(
            f'<p class="summary-detail-label">{html.escape(label)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="summary-detail-body">{html.escape(wrapped)}</div>',
            unsafe_allow_html=True,
        )


def render_selection_summary(
    provinces, sigungu, daebunryu, jungbunryu, period_summary
) -> None:
    compact = _compact_sections(
        provinces, sigungu, daebunryu, jungbunryu, period_summary
    )
    full = _full_sections(
        provinces, sigungu, daebunryu, jungbunryu, period_summary
    )

    _render_vertical_summary(compact)

    with st.expander("선택 상세 펼치기", expanded=False):
        _render_expanded_detail(full)
