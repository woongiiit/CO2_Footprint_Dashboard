import html
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components.filter_multiselect import filter_multiselect
from components.period_range_select import period_range_select
from components.analytics_dashboard import render_analytics_dashboard
from components.map_view import render_map
from config import DATA_DIR
from services.chart_data import prepare_chart_bundle
from services.data_service import (
    aggregate_for_map,
    build_filtered_dataset,
    get_daebunryu_options,
    get_jungbunryu_options_for_daebunryu,
    get_province_options,
    get_sigungu_options_for_provinces,
    list_periods,
    periods_in_range,
    resolve_period_keys,
    resolve_sigungu_filter,
    resolve_upjong_filter,
)


def inject_styles():
    st.markdown(
        """
        <style>
        .dashboard-banner {
            background: linear-gradient(90deg, #0d3d2e 0%, #1a7f4e 100%);
            padding: 1.1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.2rem;
        }
        .dashboard-banner h1 {
            color: #ffffff;
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0;
            text-align: left;
        }
        .panel-box {
            background: #f8faf9;
            border: 1px solid #e0ebe6;
            border-radius: 8px;
            padding: 1rem;
            min-height: 120px;
        }
        .summary-box {
            background: #ffffff;
            border: 1px dashed #b8d4c8;
            border-radius: 6px;
            padding: 0.85rem 0.95rem;
        }
        .summary-item {
            margin-bottom: 0.7rem;
        }
        .summary-item:last-child {
            margin-bottom: 0;
        }
        .summary-item-label {
            color: #31333f;
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 0.25rem;
        }
        .summary-item-value {
            color: #5c5f6a;
            font-size: 0.875rem;
            font-weight: 400;
            line-height: 1.55;
            word-break: keep-all;
        }
        /* 필터 드롭다운 */
        .filter-field-label {
            color: #31333f;
            font-size: 0.95rem;
            font-weight: 500;
            margin: 0.35rem 0 0.3rem 0;
        }
        .filter-trigger-disabled {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 0.55rem 0.75rem;
            color: #9aa0a6;
            font-size: 0.9rem;
            background: #f5f5f5;
            margin-bottom: 0.35rem;
        }
        .filter-popover-wrap [data-testid="stPopover"] > button {
            width: 100% !important;
            justify-content: space-between !important;
            border: 1px solid #f25c54 !important;
            border-radius: 6px !important;
            background: #fff !important;
            color: #9aa0a6 !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
            padding: 0.55rem 0.75rem !important;
            box-shadow: none !important;
            margin-bottom: 0.35rem;
        }
        .filter-popover-wrap [data-testid="stPopover"] > button p {
            color: inherit !important;
            font-size: 0.9rem !important;
        }
        .filter-popover-wrap.has-selection [data-testid="stPopover"] > button,
        .filter-popover-wrap.has-selection [data-testid="stPopover"] > button p {
            color: #31333f !important;
        }
        div[data-testid="stPopoverBody"] {
            min-width: min(100%, 480px) !important;
            padding: 0 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
        }
        div[data-testid="stPopoverBody"] > div {
            padding: 0.5rem 0.75rem 0.75rem !important;
        }
        div[data-testid="stPopoverBody"] [data-testid="stCheckbox"]:first-of-type {
            background: #f3f4f6;
            margin: -0.5rem -0.75rem 0.25rem -0.75rem;
            padding: 0.5rem 0.75rem;
            border-radius: 8px 8px 0 0;
            width: calc(100% + 1.5rem);
        }
        div[data-testid="stPopoverBody"] [data-testid="stCheckbox"]:first-of-type label p {
            font-size: 0.9rem !important;
        }
        hr.filter-divider {
            margin: 0.5rem 0 0.65rem 0;
            border: none;
            border-top: 1px solid #e8e8e8;
        }
        div[data-testid="stPopoverBody"] [data-testid="column"] label p {
            font-size: 0.88rem !important;
        }
        .filter-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
        }
        .filter-header-row h4 {
            margin: 0;
            flex: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_banner():
    st.markdown(
        '<div class="dashboard-banner"><h1>탄소발자국 대시보드</h1></div>',
        unsafe_allow_html=True,
    )


def format_period_label_short(period_key: str) -> str:
    return f"{period_key[2:4]}년 {int(period_key[4:6])}월"


def format_period_range_summary(
    start_key: str | None, end_key: str | None
) -> str:
    if not start_key and not end_key:
        return "미선택"
    start = start_key or end_key
    end = end_key or start_key
    if start > end:
        start, end = end, start
    if start == end:
        return format_period_label_short(start)
    return f"{format_period_label_short(start)} ~ {format_period_label_short(end)}"


def _apply_filters_from_draft() -> None:
    st.session_state["applied_provinces"] = list(
        st.session_state.get("filter_provinces", [])
    )
    st.session_state["applied_sigungu"] = list(st.session_state.get("filter_sigungu", []))
    st.session_state["applied_daebunryu"] = list(
        st.session_state.get("filter_daebunryu", [])
    )
    st.session_state["applied_jungbunryu"] = list(
        st.session_state.get("filter_jungbunryu", [])
    )
    st.session_state["applied_period_start"] = st.session_state.get(
        "filter_period_range_start"
    )
    st.session_state["applied_period_end"] = st.session_state.get(
        "filter_period_range_end"
    )
    st.session_state["filters_applied"] = True


def _applied_filter_key(period_keys: list[str]) -> tuple:
    return (
        tuple(st.session_state.get("applied_provinces", [])),
        tuple(st.session_state.get("applied_sigungu", [])),
        tuple(st.session_state.get("applied_daebunryu", [])),
        tuple(st.session_state.get("applied_jungbunryu", [])),
        tuple(
            periods_in_range(
                st.session_state.get("applied_period_start"),
                st.session_state.get("applied_period_end"),
                period_keys,
            )
        ),
    )


def _applied_period_summary() -> str:
    return format_period_range_summary(
        st.session_state.get("applied_period_start"),
        st.session_state.get("applied_period_end"),
    )


def format_sigungu_label(full_name: str, province_count: int) -> str:
    if province_count == 1 and " " in full_name:
        return full_name.split(" ", 1)[1]
    return full_name


def _summary_sections(
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


def build_selection_summary(
    provinces, sigungu, daebunryu, jungbunryu, period_summary
) -> str:
    lines = [f"{label}: {value}" for label, value in _summary_sections(
        provinces, sigungu, daebunryu, jungbunryu, period_summary
    )]
    return "\n".join(lines)


def render_selection_summary(
    provinces, sigungu, daebunryu, jungbunryu, period_summary
) -> None:
    blocks = []
    for label, value in _summary_sections(
        provinces, sigungu, daebunryu, jungbunryu, period_summary
    ):
        blocks.append(
            f'<div class="summary-item">'
            f'<div class="summary-item-label">{html.escape(label)}</div>'
            f'<div class="summary-item-value">{html.escape(value)}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="summary-box">{"".join(blocks)}</div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_dataset(
    provinces: tuple,
    sigungu: tuple,
    daebunryu: tuple,
    jungbunryu: tuple,
    periods: tuple,
):
    resolved_sigungu = resolve_sigungu_filter(list(provinces), list(sigungu))
    resolved_upjong = resolve_upjong_filter(list(daebunryu), list(jungbunryu))
    return build_filtered_dataset(
        resolved_sigungu, resolved_upjong, list(periods)
    )


@st.cache_data(show_spinner=False)
def cached_chart_bundle(
    provinces: tuple,
    sigungu: tuple,
    daebunryu: tuple,
    jungbunryu: tuple,
    periods: tuple,
):
    resolved_sigungu = resolve_sigungu_filter(list(provinces), list(sigungu))
    resolved_upjong = resolve_upjong_filter(list(daebunryu), list(jungbunryu))
    carbon_df = build_filtered_dataset(
        resolved_sigungu, resolved_upjong, list(periods)
    )
    period_keys = resolve_period_keys(list(periods))
    return prepare_chart_bundle(carbon_df, period_keys, resolved_sigungu)


def main():
    st.set_page_config(
        page_title="탄소발자국 대시보드",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    render_banner()

    if not DATA_DIR.exists():
        st.error(f"데이터 폴더를 찾을 수 없습니다: {DATA_DIR}")
        st.stop()

    period_options = list_periods()
    period_keys = [p[0] for p in period_options]

    province_options = get_province_options()
    daebunryu_options = get_daebunryu_options()

    col_filters, col_main = st.columns([1, 2.85], gap="medium")

    with col_filters:
        hdr_title, hdr_btn = st.columns([4, 1], vertical_alignment="center")
        with hdr_title:
            st.markdown("#### 필터 선택")
        with hdr_btn:
            if st.button("적용", type="primary", use_container_width=True, key="filter_apply_btn"):
                _apply_filters_from_draft()

        selected_provinces = filter_multiselect(
            "도",
            options=province_options,
            key="filter_provinces",
            placeholder="도를 선택하세요 (복수 선택 가능)",
        )
        sigungu_options = get_sigungu_options_for_provinces(selected_provinces)
        selected_sigungu = filter_multiselect(
            "시군구",
            options=sigungu_options,
            key="filter_sigungu",
            format_func=lambda x: format_sigungu_label(x, len(selected_provinces)),
            placeholder=(
                "도를 먼저 선택하세요"
                if not selected_provinces
                else "시군구를 선택하세요 (복수 선택 가능)"
            ),
            disabled=not selected_provinces,
        )
        selected_daebunryu = filter_multiselect(
            "업종(대분류)",
            options=daebunryu_options,
            key="filter_daebunryu",
            placeholder="대분류를 선택하세요 (복수 선택 가능)",
        )
        jungbunryu_options = get_jungbunryu_options_for_daebunryu(selected_daebunryu)
        selected_jungbunryu = filter_multiselect(
            "업종(중분류)",
            options=jungbunryu_options,
            key="filter_jungbunryu",
            placeholder=(
                "대분류를 먼저 선택하세요"
                if not selected_daebunryu
                else "중분류를 선택하세요 (복수 선택 가능)"
            ),
            disabled=not selected_daebunryu,
        )
        period_start, period_end = period_range_select(
            "기간",
            period_options=period_options,
        )
        period_summary = format_period_range_summary(period_start, period_end)

        st.markdown("##### 선택 요약")
        if st.session_state.get("filters_applied"):
            render_selection_summary(
                st.session_state.get("applied_provinces", []),
                st.session_state.get("applied_sigungu", []),
                st.session_state.get("applied_daebunryu", []),
                st.session_state.get("applied_jungbunryu", []),
                _applied_period_summary(),
            )
        else:
            render_selection_summary(
                selected_provinces,
                selected_sigungu,
                selected_daebunryu,
                selected_jungbunryu,
                period_summary,
            )

    with col_main:
        if not st.session_state.get("filters_applied"):
            st.info("필터를 선택한 뒤 **[적용]** 버튼을 눌러 주세요.")
        else:
            filter_key = _applied_filter_key(period_keys)
            carbon_df = cached_dataset(*filter_key)
            chart_bundle = cached_chart_bundle(*filter_key)
            map_df = aggregate_for_map(carbon_df)
            total_t = (
                carbon_df["총_탄소발자국(t_CO2eq)"].sum()
                if not carbon_df.empty
                else 0.0
            )
            region_count = (
                carbon_df["시군구"].nunique() if not carbon_df.empty else 0
            )

            tab_charts, tab_map = st.tabs(["차트", "지도"])
            with tab_charts:
                render_analytics_dashboard(chart_bundle, total_t, region_count)
            with tab_map:
                render_map(map_df, height=620)


if __name__ == "__main__":
    main()
