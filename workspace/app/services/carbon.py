import pandas as pd

EMISSION_FACTORS_PER_10K = {
    "항공운송": 3.50,
    "수상운송": 2.80,
    "렌터카": 2.20,
    "육상운송": 1.50,
    "일반외식업": 1.60,
    "제과음료업": 1.20,
    "호텔": 1.40,
    "콘도": 1.20,
    "스키장": 1.80,
    "기타숙박": 0.90,
    "캠핑장/펜션": 0.70,
    "대형쇼핑몰": 0.85,
    "면세점": 0.80,
    "레저용품쇼핑": 0.75,
    "기타관광쇼핑": 0.70,
    "골프장": 0.65,
    "관광유원시설": 0.60,
    "기타레저": 0.50,
    "문화서비스": 0.40,
    "의료관광": 0.45,
    "뷰티": 0.35,
    "여행업": 0.15,
}

EF_PER_WON = {k: v / 10000.0 for k, v in EMISSION_FACTORS_PER_10K.items()}
UPJONG_LIST = list(EMISSION_FACTORS_PER_10K.keys())


def calculate_carbon_footprint(df: pd.DataFrame) -> pd.DataFrame:
    result_df = pd.DataFrame()
    result_df["시군구"] = df["시군구"]

    carbon_col_names = []
    for upjong, ef in EF_PER_WON.items():
        if upjong in df.columns:
            col_name = f"{upjong}_탄소발자국(kg_CO2eq)"
            result_df[col_name] = df[upjong] * ef
            carbon_col_names.append(col_name)

    if carbon_col_names:
        result_df["총_탄소발자국(kg_CO2eq)"] = result_df[carbon_col_names].sum(axis=1)
        result_df["총_탄소발자국(t_CO2eq)"] = (
            result_df["총_탄소발자국(kg_CO2eq)"] / 1000.0
        )
        metric_cols = carbon_col_names + [
            "총_탄소발자국(kg_CO2eq)",
            "총_탄소발자국(t_CO2eq)",
        ]
        result_df[metric_cols] = result_df[metric_cols].round(2)

    return result_df


def filter_by_upjong(carbon_df: pd.DataFrame, upjong_list: list[str]) -> pd.DataFrame:
    if not upjong_list:
        return carbon_df

    cols = ["시군구"]
    if "기간" in carbon_df.columns:
        cols.append("기간")
    for upjong in upjong_list:
        col = f"{upjong}_탄소발자국(kg_CO2eq)"
        if col in carbon_df.columns:
            cols.append(col)

    filtered = carbon_df[cols].copy()
    kg_cols = [c for c in cols if c.endswith("kg_CO2eq)")]
    if kg_cols:
        filtered["총_탄소발자국(kg_CO2eq)"] = filtered[kg_cols].sum(axis=1)
        filtered["총_탄소발자국(t_CO2eq)"] = filtered["총_탄소발자국(kg_CO2eq)"] / 1000.0
        filtered[["총_탄소발자국(kg_CO2eq)", "총_탄소발자국(t_CO2eq)"]] = filtered[
            ["총_탄소발자국(kg_CO2eq)", "총_탄소발자국(t_CO2eq)"]
        ].round(2)
    return filtered
