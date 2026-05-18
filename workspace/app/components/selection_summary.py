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


def _render_compact_row(sections: list[tuple[str, str]]) -> None:
    cols = st.columns(len(sections))
    for col, (label, value) in zip(cols, sections):
        with col:
            st.markdown(
                f'<p class="summary-inline-label">{html.escape(label)}</p>'
                f'<p class="summary-inline-value">{html.escape(value)}</p>',
                unsafe_allow_html=True,
            )


def _render_expanded_detail(sections: list[tuple[str, str]]) -> None:
    for label, value in sections:
        st.markdown(
            f'<p class="summary-detail-label">{html.escape(label)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="summary-detail-body">{html.escape(value)}</div>',
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

    _render_compact_row(compact)

    with st.expander("선택 상세 펼치기", expanded=False):
        _render_expanded_detail(full)
