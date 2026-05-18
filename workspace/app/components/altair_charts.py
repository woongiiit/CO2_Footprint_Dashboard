"""Altair 기반 차트 — 도넛·기간 추이 (가독성 개선)."""

import altair as alt
import pandas as pd
import streamlit as st

PALETTE = [
    "#1a7f4e",
    "#3b82c6",
    "#e67e22",
    "#f25c54",
    "#14b8a6",
    "#8b5cf6",
    "#f59e0b",
]


def _empty_message(title: str) -> None:
    st.markdown(f"**{title}**")
    st.caption("표시할 데이터가 없습니다.")


def render_daebunryu_donut(df: pd.DataFrame, total_t: float | None = None) -> None:
    title = "업종(대분류) 비중"
    if df.empty:
        _empty_message(title)
        return

    data = df.copy()
    total = total_t if total_t is not None else data["탄소발자국(t)"].sum()
    data["비율"] = data["탄소발자국(t)"] / total
    data["라벨"] = data["비율"].apply(lambda p: f"{p:.0%}" if p >= 0.04 else "")
    data = data.sort_values("탄소발자국(t)", ascending=False)

    base = alt.Chart(data).encode(
        theta=alt.Theta("탄소발자국(t):Q", stack=True),
        color=alt.Color(
            "대분류:N",
            scale=alt.Scale(range=PALETTE),
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                title=None,
                labelFontSize=10,
                symbolSize=80,
                columns=3,
            ),
        ),
        tooltip=[
            alt.Tooltip("대분류:N", title="대분류"),
            alt.Tooltip("탄소발자국(t):Q", title="t CO₂eq", format=",.1f"),
            alt.Tooltip("비율:Q", title="비율", format=".1%"),
        ],
    )

    donut = base.mark_arc(innerRadius=70, outerRadius=125, stroke="#fff", strokeWidth=1.5)

    labels = base.mark_text(radius=138, size=10, color="#31333f").encode(
        text="라벨:N",
    )

    chart = (
        (donut + labels)
        .properties(width="container", height=300, title=title)
        .configure_view(strokeWidth=0)
        .configure_title(fontSize=13, anchor="start", color="#31333f")
    )

    st.caption(f"합계 {total:,.0f} t CO₂eq")
    st.altair_chart(chart, use_container_width=True)


def render_period_trend(df: pd.DataFrame) -> None:
    title = "기간별·대분류 추이"
    if df.empty:
        _empty_message(title)
        return

    data = (
        df.groupby(["기간", "기간라벨", "대분류"], as_index=False)["탄소발자국(t)"]
        .sum()
        .sort_values("기간")
    )

    period_order = (
        data.sort_values("기간")[["기간라벨"]]
        .drop_duplicates()["기간라벨"]
        .tolist()
    )

    chart = (
        alt.Chart(data)
        .mark_area(
            opacity=0.88,
            interpolate="monotone",
            line={"color": "white", "strokeWidth": 0.6},
        )
        .encode(
            x=alt.X(
                "기간라벨:N",
                sort=period_order,
                title=None,
                axis=alt.Axis(labelAngle=-35, labelFontSize=10, labelPadding=6),
            ),
            y=alt.Y(
                "탄소발자국(t):Q",
                stack="zero",
                title="t CO₂eq",
                axis=alt.Axis(format="~s", labelFontSize=10),
            ),
            color=alt.Color(
                "대분류:N",
                scale=alt.Scale(range=PALETTE),
                legend=alt.Legend(
                    orient="right",
                    title=None,
                    labelFontSize=9,
                    symbolSize=70,
                    offset=8,
                ),
            ),
            tooltip=[
                alt.Tooltip("기간라벨:N", title="기간"),
                alt.Tooltip("대분류:N", title="대분류"),
                alt.Tooltip("탄소발자국(t):Q", title="t CO₂eq", format=",.1f"),
            ],
        )
        .properties(width="container", height=300, title=title)
        .configure_view(strokeWidth=0)
        .configure_title(fontSize=13, anchor="start", color="#31333f")
        .configure_axis(gridColor="#e8ece9")
    )

    st.altair_chart(chart, use_container_width=True)
