import html
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components.filter_multiselect import filter_multiselect
from components.map_view import render_map
from config import DATA_DIR
from services.data_service import (
    aggregate_for_insights,
    aggregate_for_map,
    build_filtered_dataset,
    get_daebunryu_options,
    get_jungbunryu_options_for_daebunryu,
    get_province_options,
    get_sigungu_options_for_provinces,
    list_periods,
    resolve_sigungu_filter,
    resolve_upjong_filter,
)
from services.insights import generate_ai_content


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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_banner():
    st.markdown(
        '<div class="dashboard-banner"><h1>탄소발자국 대시보드</h1></div>',
        unsafe_allow_html=True,
    )


def format_period_label(period_key: str) -> str:
    return f"{period_key[:4]}년 {int(period_key[4:6])}월"


def format_sigungu_label(full_name: str, province_count: int) -> str:
    if province_count == 1 and " " in full_name:
        return full_name.split(" ", 1)[1]
    return full_name


def _summary_sections(
    provinces, sigungu, daebunryu, jungbunryu, periods
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
    per = ", ".join(format_period_label(p) for p in periods) if periods else "전체"
    return [
        ("도", prov),
        ("시군구", sig),
        ("업종(대분류)", dae),
        ("업종(중분류)", jung),
        ("기간", per),
    ]


def build_selection_summary(
    provinces, sigungu, daebunryu, jungbunryu, periods
) -> str:
    lines = [f"{label}: {value}" for label, value in _summary_sections(
        provinces, sigungu, daebunryu, jungbunryu, periods
    )]
    return "\n".join(lines)


def render_selection_summary(
    provinces, sigungu, daebunryu, jungbunryu, periods
) -> None:
    blocks = []
    for label, value in _summary_sections(
        provinces, sigungu, daebunryu, jungbunryu, periods
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
    period_labels = {p[0]: p[1] for p in period_options}

    province_options = get_province_options()
    daebunryu_options = get_daebunryu_options()

    col_left, col_center, col_right = st.columns([1.1, 1.4, 1.5], gap="medium")

    with col_left:
        st.markdown("#### 필터 선택")
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
        selected_periods = filter_multiselect(
            "기간",
            options=period_keys,
            key="filter_periods",
            format_func=lambda k: period_labels.get(k, k),
            placeholder="기간을 선택하세요 (복수 선택 가능)",
        )

        selection_text = build_selection_summary(
            selected_provinces,
            selected_sigungu,
            selected_daebunryu,
            selected_jungbunryu,
            selected_periods,
        )
        st.markdown("##### 선택 요약")
        render_selection_summary(
            selected_provinces,
            selected_sigungu,
            selected_daebunryu,
            selected_jungbunryu,
            selected_periods,
        )

    carbon_df = cached_dataset(
        tuple(selected_provinces),
        tuple(selected_sigungu),
        tuple(selected_daebunryu),
        tuple(selected_jungbunryu),
        tuple(selected_periods),
    )
    map_df = aggregate_for_map(carbon_df)
    stats = aggregate_for_insights(carbon_df)

    with col_center:
        st.markdown("#### AI 분석")
        if carbon_df.empty:
            st.warning("표시할 데이터가 없습니다. 왼쪽에서 조건을 선택해 주세요.")
        else:
            if st.button("AI 요약·인사이트 생성", type="primary", use_container_width=True):
                with st.spinner("Hugging Face 모델로 분석 중..."):
                    summary, insights = generate_ai_content(stats, selection_text)
                st.session_state["ai_summary"] = summary
                st.session_state["ai_insights"] = insights

            summary = st.session_state.get("ai_summary")
            insights = st.session_state.get("ai_insights")

            if summary:
                st.markdown("**결과 요약**")
                st.markdown(
                    f'<div class="panel-box">{html.escape(summary)}</div>',
                    unsafe_allow_html=True,
                )
            if insights:
                st.markdown("**고려할 인사이트**")
                st.markdown(
                    f'<div class="panel-box">{html.escape(insights)}</div>',
                    unsafe_allow_html=True,
                )
            if not summary and not insights:
                st.info(
                    "「AI 요약·인사이트 생성」 버튼을 누르면 Hugging Face API로 "
                    "선택 조건에 대한 요약과 인사이트를 생성합니다."
                )

            if stats:
                st.caption(
                    f"총 {stats.get('total_t_co2eq', 0):,.2f} t CO2eq · "
                    f"{stats.get('region_count', 0)}개 지역"
                )

    with col_right:
        st.markdown("#### 지역별 탄소발자국 지도")
        render_map(map_df)


if __name__ == "__main__":
    main()
