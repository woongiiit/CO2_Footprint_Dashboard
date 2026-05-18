import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CHART_HEIGHT = 300
COLORS = {
    "primary": "#1a7f4e",
    "secondary": "#2ecc71",
    "accent": "#f25c54",
    "blue": "#3b82c6",
    "orange": "#e67e22",
    "teal": "#14b8a6",
    "palette": ["#1a7f4e", "#3b82c6", "#e67e22", "#f25c54", "#14b8a6", "#8b5cf6", "#f59e0b"],
}
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, font=dict(size=13)),
        height=CHART_HEIGHT,
        margin=dict(l=40, r=20, t=40, b=30),
        annotations=[
            dict(
                text="데이터 없음",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=12, color="#9aa0a6"),
            )
        ],
    )
    return fig


def _chart_title(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#31333f"), x=0),
        height=CHART_HEIGHT,
        margin=dict(l=10, r=10, t=36, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=11, color="#5c5f6a"),
    )
    return fig


def chart_province_bar(df: pd.DataFrame) -> go.Figure:
    title = "시도별 탄소발자국"
    if df.empty:
        return _empty_fig(title)
    top_n = min(12, len(df))
    data = df.tail(top_n).copy()
    bar_colors = [
        COLORS["blue"] if i >= len(data) - 2 else COLORS["orange"]
        for i in range(len(data))
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=data["시도"],
            x=data["탄소발자국"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:,.0f}" for v in data["탄소발자국"]],
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    vmin, vmax = df["탄소발자국"].min(), df["탄소발자국"].max()
    fig.add_vrect(
        x0=vmin,
        x1=vmax,
        fillcolor="rgba(180,180,180,0.15)",
        line_width=0,
        layer="below",
    )
    fig.update_layout(
        xaxis_title="탄소발자국 (t CO2eq)",
        yaxis=dict(autorange="reversed"),
        showlegend=False,
    )
    return _chart_title(fig, title)


def chart_energy_scatter(df: pd.DataFrame) -> go.Figure:
    title = "에너지소비량 vs 탄소발자국 (주요 대분류)"
    if df.empty:
        return _empty_fig(title)
    fig = px.scatter(
        df,
        x="에너지소비량(억원)",
        y="총_탄소발자국(t_CO2eq)",
        color="주요대분류",
        hover_name="시군구",
        color_discrete_sequence=COLORS["palette"],
        trendline="ols",
        trendline_scope="trace",
    )
    fig.update_traces(marker=dict(size=7, opacity=0.75))
    fig.update_layout(
        xaxis_title="에너지소비량 (억원)",
        yaxis_title="탄소발자국 (t CO2eq)",
        legend=dict(
            title="",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9),
        ),
    )
    return _chart_title(fig, title)


def chart_period_stack(df: pd.DataFrame) -> go.Figure:
    title = "기간별·대분류별 탄소발자국 추이"
    if df.empty:
        return _empty_fig(title)
    period_order = (
        list(df["기간라벨"].cat.categories)
        if hasattr(df["기간라벨"], "cat")
        else sorted(df["기간라벨"].unique())
    )
    fig = px.area(
        df,
        x="기간라벨",
        y="탄소발자국(t)",
        color="대분류",
        color_discrete_sequence=COLORS["palette"],
        category_orders={"기간라벨": period_order},
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="탄소발자국 (t CO2eq)",
        legend=dict(
            title="",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9),
        ),
    )
    return _chart_title(fig, title)


def chart_intensity_groups(df: pd.DataFrame) -> go.Figure:
    title = "탄소집약도 상·하위 지역"
    if df.empty:
        return _empty_fig(title)
    colors = {"상위": COLORS["accent"], "하위": COLORS["blue"]}
    fig = go.Figure()
    for group in ["상위", "하위"]:
        sub = df[df["집단"] == group].sort_values("탄소집약도", ascending=True)
        fig.add_trace(
            go.Bar(
                y=sub["라벨"],
                x=sub["탄소집약도"],
                name=group,
                orientation="h",
                marker_color=colors[group],
                text=[f"{v:.3f}" for v in sub["탄소집약도"]],
                textposition="outside",
                textfont=dict(size=9),
            )
        )
    fig.update_layout(
        barmode="group",
        xaxis_title="탄소집약도 (t / 억원)",
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    return _chart_title(fig, title)


def chart_daebunryu_donut(df: pd.DataFrame) -> go.Figure:
    title = "업종(대분류)별 비중"
    if df.empty:
        return _empty_fig(title)
    total = df["탄소발자국(t)"].sum()
    fig = go.Figure(
        go.Pie(
            labels=df["대분류"],
            values=df["탄소발자국(t)"],
            hole=0.55,
            marker_colors=COLORS["palette"],
            textinfo="percent+label",
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"{total:,.0f}<br><span style='font-size:10px'>t CO2eq</span>",
                x=0.5,
                y=0.5,
                font_size=14,
                showarrow=False,
            )
        ],
        showlegend=False,
    )
    return _chart_title(fig, title)


def chart_region_treemap(df: pd.DataFrame) -> go.Figure:
    title = "시도별 탄소발자국 규모"
    if df.empty:
        return _empty_fig(title)
    prov = (
        df.groupby("시도", as_index=False)["총_탄소발자국(t_CO2eq)"]
        .sum()
        .round(2)
        .sort_values("총_탄소발자국(t_CO2eq)", ascending=False)
    )
    fig = px.treemap(
        prov,
        path=["시도"],
        values="총_탄소발자국(t_CO2eq)",
        color="총_탄소발자국(t_CO2eq)",
        color_continuous_scale=["#d4ede4", "#1a7f4e"],
    )
    fig.update_traces(textinfo="label+value")
    fig.update_layout(coloraxis_showscale=False)
    return _chart_title(fig, title)


def render_analytics_dashboard(bundle: dict, total_t: float, region_count: int) -> None:
    region_df = bundle.get("region", pd.DataFrame())
    if region_df.empty:
        st.warning("표시할 데이터가 없습니다. 필터에서 조건을 선택해 주세요.")
        return

    st.caption(
        f"총 {total_t:,.2f} t CO2eq · {region_count}개 시군구 · "
        f"필터 조건 기준 집계"
    )

    charts = [
        chart_province_bar(bundle["by_province"]),
        chart_energy_scatter(bundle["scatter"]),
        chart_period_stack(bundle["period_stack"]),
        chart_intensity_groups(bundle["top_bottom"]),
        chart_daebunryu_donut(bundle["by_daebunryu"]),
        chart_region_treemap(bundle["region"]),
    ]
    for i in range(0, len(charts), 2):
        col_left, col_right = st.columns(2, gap="medium")
        with col_left:
            st.plotly_chart(charts[i], use_container_width=True, config=PLOT_CONFIG)
        with col_right:
            st.plotly_chart(charts[i + 1], use_container_width=True, config=PLOT_CONFIG)
