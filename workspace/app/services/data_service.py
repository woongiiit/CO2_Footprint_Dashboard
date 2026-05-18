from pathlib import Path

import pandas as pd

from config import DATA_DIR, PROJECT_ROOT
from services.carbon import UPJONG_LIST, calculate_carbon_footprint, filter_by_upjong

SIGUNGU_FIELD_PATH = (
    PROJECT_ROOT / "datas" / "data_generator" / "시군구 필드.csv"
)
UPJONG_FIELD_PATH = PROJECT_ROOT / "datas" / "data_generator" / "업종 필드.csv"


def list_periods() -> list[tuple[str, str]]:
    files = sorted(DATA_DIR.glob("관광소비지출_*.csv"))
    periods = []
    for f in files:
        stem = f.stem.replace("관광소비지출_", "")
        label = f"{stem[:4]}년 {int(stem[4:6])}월"
        periods.append((stem, label))
    return periods


def resolve_period_keys(period_keys: list[str]) -> list[str]:
    if period_keys:
        return period_keys
    return [p[0] for p in list_periods()]


def periods_in_range(
    start_key: str | None,
    end_key: str | None,
    available: list[str] | None = None,
) -> list[str]:
    if not start_key and not end_key:
        return []
    start = start_key or end_key
    end = end_key or start_key
    if start > end:
        start, end = end, start
    if available is None:
        available = [p[0] for p in list_periods()]
    return [p for p in available if start <= p <= end]


def load_spending(periods: list[str]) -> pd.DataFrame:
    frames = []
    for period in periods:
        path = DATA_DIR / f"관광소비지출_{period}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df["기간"] = period
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def get_region_hierarchy() -> dict[str, list[str]]:
    """광역(도) → 전체 시군구명 목록 매핑."""
    if SIGUNGU_FIELD_PATH.exists():
        df = pd.read_csv(SIGUNGU_FIELD_PATH)
        hierarchy: dict[str, list[str]] = {}
        for row in df.itertuples(index=False):
            province = row[0]
            full_name = f"{province} {row[1]}"
            hierarchy.setdefault(province, []).append(full_name)
        return {k: sorted(v) for k, v in sorted(hierarchy.items())}

    sample = DATA_DIR / "관광소비지출_202505.csv"
    if not sample.exists():
        return {}
    df = pd.read_csv(sample)
    hierarchy = {}
    for name in df["시군구"].unique():
        province, _, gicho = name.partition(" ")
        hierarchy.setdefault(province, []).append(name)
    return {k: sorted(v) for k, v in sorted(hierarchy.items())}


def get_province_options() -> list[str]:
    return list(get_region_hierarchy().keys())


def get_sigungu_options_for_provinces(provinces: list[str]) -> list[str]:
    hierarchy = get_region_hierarchy()
    if not provinces:
        return []
    options = []
    for province in provinces:
        options.extend(hierarchy.get(province, []))
    return sorted(set(options))


def resolve_sigungu_filter(
    provinces: list[str], selected_sigungu: list[str]
) -> list[str]:
    if provinces and selected_sigungu:
        return selected_sigungu
    if provinces:
        return get_sigungu_options_for_provinces(provinces)
    return selected_sigungu


def get_upjong_hierarchy() -> dict[str, list[str]]:
    """대분류 → 중분류 목록 매핑."""
    if UPJONG_FIELD_PATH.exists():
        df = pd.read_csv(UPJONG_FIELD_PATH)
        hierarchy: dict[str, list[str]] = {}
        for row in df.itertuples(index=False):
            hierarchy.setdefault(row[0], []).append(row[1])
        return {k: sorted(v) for k, v in sorted(hierarchy.items())}

    hierarchy: dict[str, list[str]] = {}
    for jung in UPJONG_LIST:
        hierarchy.setdefault("기타", []).append(jung)
    return hierarchy


def get_daebunryu_options() -> list[str]:
    return list(get_upjong_hierarchy().keys())


def get_jungbunryu_options_for_daebunryu(daebunryu_list: list[str]) -> list[str]:
    hierarchy = get_upjong_hierarchy()
    if not daebunryu_list:
        return []
    options = []
    for dae in daebunryu_list:
        options.extend(hierarchy.get(dae, []))
    return sorted(set(options))


def resolve_upjong_filter(
    daebunryu_list: list[str], selected_jungbunryu: list[str]
) -> list[str]:
    if daebunryu_list and selected_jungbunryu:
        return selected_jungbunryu
    if daebunryu_list:
        return get_jungbunryu_options_for_daebunryu(daebunryu_list)
    return selected_jungbunryu


def build_filtered_dataset(
    sigungu_list: list[str],
    upjong_list: list[str],
    period_keys: list[str],
) -> pd.DataFrame:
    if not period_keys and not sigungu_list and not upjong_list:
        return pd.DataFrame()

    period_keys = resolve_period_keys(period_keys)

    spending = load_spending(period_keys)
    if spending.empty:
        return pd.DataFrame()

    if sigungu_list:
        spending = spending[spending["시군구"].isin(sigungu_list)]

    carbon_rows = []
    for period in spending["기간"].unique():
        period_df = spending[spending["기간"] == period].drop(columns=["기간"])
        carbon = calculate_carbon_footprint(period_df)
        carbon["기간"] = period
        carbon_rows.append(carbon)

    carbon_df = pd.concat(carbon_rows, ignore_index=True)
    if upjong_list:
        carbon_df = filter_by_upjong(carbon_df, upjong_list)

    return carbon_df


def aggregate_for_map(carbon_df: pd.DataFrame) -> pd.DataFrame:
    if carbon_df.empty:
        return pd.DataFrame(columns=["시군구", "총_탄소발자국(t_CO2eq)"])

    agg = (
        carbon_df.groupby("시군구", as_index=False)["총_탄소발자국(t_CO2eq)"]
        .sum()
        .round(2)
    )
    return agg


def aggregate_for_insights(carbon_df: pd.DataFrame) -> dict:
    if carbon_df.empty:
        return {}

    total_t = carbon_df["총_탄소발자국(t_CO2eq)"].sum()
    by_region = (
        carbon_df.groupby("시군구")["총_탄소발자국(t_CO2eq)"]
        .sum()
        .sort_values(ascending=False)
    )
    top5 = by_region.head(5)

    upjong_cols = [c for c in carbon_df.columns if c.endswith("_탄소발자국(kg_CO2eq)")]
    by_upjong = {}
    if upjong_cols:
        sums = carbon_df[upjong_cols].sum().sort_values(ascending=False)
        by_upjong = {
            c.replace("_탄소발자국(kg_CO2eq)", ""): round(v / 1000, 2)
            for c, v in sums.head(5).items()
        }

    return {
        "total_t_co2eq": round(total_t, 2),
        "region_count": carbon_df["시군구"].nunique(),
        "period_count": carbon_df["기간"].nunique() if "기간" in carbon_df.columns else 1,
        "top_regions": {k: round(v, 2) for k, v in top5.items()},
        "top_upjong_t": by_upjong,
    }
