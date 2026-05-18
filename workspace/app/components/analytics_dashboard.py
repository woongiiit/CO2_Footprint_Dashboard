import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.altair_charts import render_daebunryu_donut, render_period_trend

CHART_HEIGHT = 320
CHART_HEIGHT_COMPACT = 210
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

MAX_SCATTER_POINTS = 45
MAX_BAR_ROWS = 8
MAX_INTENSITY_ROWS = 5


def _dynamic_bar_height(row_count: int, compact: bool) -> int:
    rows = max(1, min(row_count, MAX_BAR_ROWS if compact else 12))
    if compact:
        return min(340, 100 + rows * 26)
    return min(480, 140 + rows * 30)


def _layout_kwargs(
    compact: bool,
    *,
    height: int | None = None,
    legend_rows: int = 0,
) -> dict:
    extra_bottom = 28 + legend_rows * 18
    if compact:
        return dict(
            height=height or CHART_HEIGHT_COMPACT,
            margin=dict(l=52, r=20, t=48, b=40 + extra_bottom),
        )
    return dict(
        height=height or CHART_HEIGHT,
        margin=dict(l=10, r=10, t=36, b=10 + extra_bottom),
    )


def _apply_legend_below(fig: go.Figure, compact: bool, n_items: int = 0) -> None:
    if n_items <= 1:
        fig.update_layout(showlegend=False)
        return
    y_offset = -0.28 if compact else -0.18
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=y_offset,
            xanchor="left",
            x=0,
            font=dict(size=8),
            tracegroupgap=4,
        ),
    )


def _empty_fig(title: str, compact: bool = False) -> go.Figure:
    layout = _layout_kwargs(compact)
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, font=dict(size=12 if compact else 13)),
        annotations=[
            dict(
                text="데이터 없음",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=11, color="#9aa0a6"),
            )
        ],
        **layout,
    )
    return fig


def _chart_title(
    fig: go.Figure,
    title: str,
    compact: bool = False,
    *,
    height: int | None = None,
    legend_rows: int = 0,
) -> go.Figure:
    layout = _layout_kwargs(compact, height=height, legend_rows=legend_rows)
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=12 if compact else 13, color="#31333f"),
            x=0,
            xanchor="left",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=10 if compact else 11, color="#5c5f6a"),
        **layout,
    )
    return fig


def chart_province_bar(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "시도별 탄소발자국"
    if df.empty:
        return _empty_fig(title, compact)
    top_n = min(MAX_BAR_ROWS if compact else 12, len(df))
    data = df.nlargest(top_n, "탄소발자국").sort_values("탄소발자국", ascending=True)
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
            hovertemplate="%{y}<br>%{x:,.0f} t<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="t CO₂eq",
        yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
        showlegend=False,
    )
    h = _dynamic_bar_height(len(data), compact)
    return _chart_title(fig, title, compact, height=h)


def chart_energy_scatter(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "에너지 vs 탄소발자국"
    if df.empty:
        return _empty_fig(title, compact)
    plot_df = df.nlargest(MAX_SCATTER_POINTS, "총_탄소발자국(t_CO2eq)")
    use_trend = len(plot_df) <= 25
    fig = px.scatter(
        plot_df,
        x="에너지소비량(억원)",
        y="총_탄소발자국(t_CO2eq)",
        color="주요대분류",
        hover_name="시군구",
        color_discrete_sequence=COLORS["palette"],
        trendline="ols" if use_trend else None,
        trendline_scope="trace",
    )
    fig.update_traces(marker=dict(size=5 if compact else 6, opacity=0.7))
    n_legend = plot_df["주요대분류"].nunique()
    _apply_legend_below(fig, compact, n_legend)
    fig.update_layout(
        xaxis_title="에너지 (억원)",
        yaxis_title="t CO₂eq",
    )
    legend_rows = 1 if n_legend > 3 else 0
    return _chart_title(fig, title, compact, legend_rows=legend_rows)


def chart_period_stack(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "기간별·대분류 추이"
    if df.empty:
        return _empty_fig(title, compact)
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
    n_legend = df["대분류"].nunique()
    _apply_legend_below(fig, compact, n_legend)
    fig.update_layout(xaxis_title="", yaxis_title="t CO₂eq")
    legend_rows = 2 if n_legend > 4 else 1
    return _chart_title(fig, title, compact, legend_rows=legend_rows)


def chart_intensity_groups(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "탄소집약도 상·하위"
    if df.empty:
        return _empty_fig(title, compact)
    colors = {"상위": COLORS["accent"], "하위": COLORS["blue"]}
    fig = go.Figure()
    row_count = 0
    for group in ["상위", "하위"]:
        sub = (
            df[df["집단"] == group]
            .nlargest(MAX_INTENSITY_ROWS, "탄소집약도")
            .sort_values("탄소집약도", ascending=True)
        )
        row_count += len(sub)
        fig.add_trace(
            go.Bar(
                y=sub["라벨"],
                x=sub["탄소집약도"],
                name=group,
                orientation="h",
                marker_color=colors[group],
                hovertemplate="%{y}<br>%{x:.3f}<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="group",
        xaxis_title="t / 억원",
        yaxis=dict(autorange="reversed", tickfont=dict(size=8)),
    )
    _apply_legend_below(fig, compact, 2)
    h = _dynamic_bar_height(row_count, compact)
    return _chart_title(fig, title, compact, height=h, legend_rows=1)


def chart_daebunryu_donut(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "업종(대분류) 비중"
    if df.empty:
        return _empty_fig(title, compact)
    total = df["탄소발자국(t)"].sum()
    fig = go.Figure(
        go.Pie(
            labels=df["대분류"],
            values=df["탄소발자국(t)"],
            hole=0.55,
            marker_colors=COLORS["palette"],
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=9),
        )
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"{total:,.0f}<br><span style='font-size:9px'>t</span>",
                x=0.5,
                y=0.5,
                font_size=12 if compact else 14,
                showarrow=False,
            )
        ],
        showlegend=False,
    )
    return _chart_title(fig, title, compact)


def chart_region_treemap(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    title = "시도별 규모"
    if df.empty:
        return _empty_fig(title, compact)
    prov = (
        df.groupby("시도", as_index=False)["총_탄소발자국(t_CO2eq)"]
        .sum()
        .round(2)
        .sort_values("총_탄소발자국(t_CO2eq)", ascending=False)
        .head(12 if compact else 17)
    )
    fig = px.treemap(
        prov,
        path=["시도"],
        values="총_탄소발자국(t_CO2eq)",
        color="총_탄소발자국(t_CO2eq)",
        color_continuous_scale=["#d4ede4", "#1a7f4e"],
    )
    fig.update_traces(textinfo="label+percent parent")
    fig.update_layout(coloraxis_showscale=False)
    return _chart_title(fig, title, compact)


def render_analytics_dashboard(
    bundle: dict,
    total_t: float,
    region_count: int,
    *,
    compact: bool = True,
) -> None:
    region_df = bundle.get("region", pd.DataFrame())
    if region_df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    st.caption(f"총 {total_t:,.1f} t · {region_count}개 지역")

    st.plotly_chart(
        chart_province_bar(bundle["by_province"], compact),
        use_container_width=True,
        config=PLOT_CONFIG,
    )
    if compact:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    render_daebunryu_donut(bundle["by_daebunryu"], total_t=total_t)
    if compact:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    render_period_trend(bundle["period_stack"])
    if compact:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    plotly_charts = [
        chart_energy_scatter(bundle["scatter"], compact),
        chart_intensity_groups(bundle["top_bottom"], compact),
        chart_region_treemap(bundle["region"], compact),
    ]

    for chart in plotly_charts:
        st.plotly_chart(chart, use_container_width=True, config=PLOT_CONFIG)
        if compact:
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
