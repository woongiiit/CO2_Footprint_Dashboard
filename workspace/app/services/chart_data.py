from functools import lru_cache

import pandas as pd

from services.carbon import UPJONG_LIST
from services.data_service import UPJONG_FIELD_PATH, load_spending, resolve_period_keys


@lru_cache(maxsize=1)
def _upjong_to_daebunryu() -> dict[str, str]:
    if UPJONG_FIELD_PATH.exists():
        df = pd.read_csv(UPJONG_FIELD_PATH)
        return dict(zip(df["중분류"], df["대분류"]))
    return {u: "기타" for u in UPJONG_LIST}


def extract_province(sigungu: str) -> str:
    return sigungu.split(" ", 1)[0]


def _spending_columns(df: pd.DataFrame) -> list[str]:
    skip = {"시군구", "기간"}
    return [c for c in df.columns if c not in skip and c in UPJONG_LIST]


def _load_spending_filtered(
    period_keys: list[str], sigungu_list: list[str]
) -> pd.DataFrame:
    spending = load_spending(resolve_period_keys(period_keys))
    if spending.empty or "시군구" not in spending.columns:
        return spending
    if sigungu_list:
        spending = spending[spending["시군구"].isin(sigungu_list)]
    return spending


def build_region_metrics(
    carbon_df: pd.DataFrame,
    period_keys: list[str],
    sigungu_list: list[str],
) -> pd.DataFrame:
    if carbon_df.empty:
        return pd.DataFrame()

    spending = _load_spending_filtered(period_keys, sigungu_list)
    if spending.empty:
        return pd.DataFrame()

    spend_cols = _spending_columns(spending)
    spending = spending.copy()
    spending["총_소비지출"] = spending[spend_cols].sum(axis=1)

    spend_agg = spending.groupby("시군구", as_index=False)["총_소비지출"].sum()
    carbon_agg = (
        carbon_df.groupby("시군구", as_index=False)["총_탄소발자국(t_CO2eq)"]
        .sum()
        .round(2)
    )

    merged = spend_agg.merge(carbon_agg, on="시군구", how="inner")
    merged["시도"] = merged["시군구"].map(extract_province)
    merged["에너지소비량(억원)"] = (merged["총_소비지출"] / 1e8).round(2)
    merged["탄소집약도"] = (
        merged["총_탄소발자국(t_CO2eq)"]
        / merged["에너지소비량(억원)"].replace(0, pd.NA)
    ).round(4)
    return merged


def aggregate_by_province(region_df: pd.DataFrame) -> pd.DataFrame:
    if region_df.empty:
        return pd.DataFrame()
    agg = (
        region_df.groupby("시도", as_index=False)
        .agg(
            탄소발자국=("총_탄소발자국(t_CO2eq)", "sum"),
            에너지소비량=("에너지소비량(억원)", "sum"),
        )
        .round(2)
    )
    agg["탄소집약도"] = (agg["탄소발자국"] / agg["에너지소비량"].replace(0, pd.NA)).round(
        4
    )
    return agg.sort_values("탄소발자국", ascending=True)


def aggregate_by_upjong(carbon_df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in carbon_df.columns if c.endswith("_탄소발자국(kg_CO2eq)")]
    if not cols:
        return pd.DataFrame()
    sums = carbon_df[cols].sum()
    rows = [
        {
            "업종": c.replace("_탄소발자국(kg_CO2eq)", ""),
            "탄소발자국(t)": round(v / 1000, 2),
        }
        for c, v in sums.items()
        if v > 0
    ]
    df = pd.DataFrame(rows)
    return df.sort_values("탄소발자국(t)", ascending=False)


def aggregate_by_daebunryu(carbon_df: pd.DataFrame) -> pd.DataFrame:
    upjong_df = aggregate_by_upjong(carbon_df)
    if upjong_df.empty:
        return pd.DataFrame()
    mapping = _upjong_to_daebunryu()
    upjong_df = upjong_df.copy()
    upjong_df["대분류"] = upjong_df["업종"].map(mapping).fillna("기타")
    return (
        upjong_df.groupby("대분류", as_index=False)["탄소발자국(t)"]
        .sum()
        .round(2)
        .sort_values("탄소발자국(t)", ascending=False)
    )


def aggregate_period_by_daebunryu(
    carbon_df: pd.DataFrame,
    period_keys: list[str],
    sigungu_list: list[str],
) -> pd.DataFrame:
    if carbon_df.empty or "기간" not in carbon_df.columns:
        return pd.DataFrame()

    mapping = _upjong_to_daebunryu()
    rows = []
    for period in sorted(carbon_df["기간"].unique()):
        period_carbon = carbon_df[carbon_df["기간"] == period]
        for col in [c for c in period_carbon.columns if c.endswith("_탄소발자국(kg_CO2eq)")]:
            upjong = col.replace("_탄소발자국(kg_CO2eq)", "")
            carbon_t = period_carbon[col].sum() / 1000
            if carbon_t <= 0:
                continue
            dae = mapping.get(upjong, "기타")
            rows.append(
                {
                    "기간": period,
                    "기간라벨": f"{period[2:4]}년 {int(period[4:6])}월",
                    "대분류": dae,
                    "탄소발자국(t)": round(carbon_t, 2),
                }
            )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    order = sorted(df["기간"].unique())
    df["기간라벨"] = pd.Categorical(df["기간라벨"], categories=[f"{p[2:4]}년 {int(p[4:6])}월" for p in order], ordered=True)
    return df


def assign_dominant_daebunryu(
    period_keys: list[str],
    sigungu_list: list[str],
) -> dict[str, str]:
    spending = _load_spending_filtered(period_keys, sigungu_list)
    spend_cols = _spending_columns(spending)
    if not spend_cols:
        return {}

    mapping = _upjong_to_daebunryu()
    dominant: dict[str, str] = {}
    for sigungu, group in spending.groupby("시군구"):
        totals = {mapping.get(c, "기타"): group[c].sum() for c in spend_cols}
        dominant[sigungu] = max(totals, key=totals.get)
    return dominant


def enrich_scatter_categories(
    region_df: pd.DataFrame,
    period_keys: list[str],
    sigungu_list: list[str],
) -> pd.DataFrame:
    if region_df.empty:
        return region_df
    dominant = assign_dominant_daebunryu(period_keys, sigungu_list)
    out = region_df.copy()
    out["주요대분류"] = out["시군구"].map(dominant).fillna("기타")
    return out


def top_bottom_by_intensity(region_df: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    if region_df.empty:
        return pd.DataFrame()
    valid = region_df.dropna(subset=["탄소집약도"]).copy()
    valid = valid.sort_values("탄소집약도", ascending=False)
    top = valid.head(n).copy()
    top["집단"] = "상위"
    bottom = valid.tail(n).copy()
    bottom["집단"] = "하위"
    combined = pd.concat([top, bottom], ignore_index=True)
    combined["라벨"] = combined["시군구"].str.split(" ", n=1).str[-1]
    return combined


def prepare_chart_bundle(
    carbon_df: pd.DataFrame,
    period_keys: list[str],
    sigungu_list: list[str],
) -> dict:
    region_df = build_region_metrics(carbon_df, period_keys, sigungu_list)
    return {
        "region": region_df,
        "by_province": aggregate_by_province(region_df),
        "by_upjong": aggregate_by_upjong(carbon_df),
        "by_daebunryu": aggregate_by_daebunryu(carbon_df),
        "period_stack": aggregate_period_by_daebunryu(
            carbon_df, period_keys, sigungu_list
        ),
        "scatter": enrich_scatter_categories(region_df, period_keys, sigungu_list),
        "top_bottom": top_bottom_by_intensity(region_df),
    }
