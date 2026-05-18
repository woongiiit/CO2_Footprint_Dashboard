import json
import math
from pathlib import Path

import pandas as pd

PROVINCE_CENTERS: dict[str, tuple[float, float]] = {
    "서울특별시": (37.5665, 126.9780),
    "부산광역시": (35.1796, 129.0756),
    "대구광역시": (35.8714, 128.6014),
    "인천광역시": (37.4563, 126.7052),
    "광주광역시": (35.1595, 126.8526),
    "대전광역시": (36.3504, 127.3845),
    "울산광역시": (35.5384, 129.3114),
    "세종특별자치시": (36.4800, 127.2890),
    "경기도": (37.4138, 127.5183),
    "강원특별자치도": (37.8228, 128.1555),
    "충청북도": (36.8000, 127.7000),
    "충청남도": (36.5184, 126.8000),
    "전북특별자치도": (35.7175, 127.1530),
    "전라남도": (34.8679, 126.9910),
    "경상북도": (36.4919, 128.8889),
    "경상남도": (35.4606, 128.2132),
    "제주특별자치도": (33.4890, 126.4983),
}

_coords_cache: dict[str, tuple[float, float]] | None = None

CENTROIDS_PATH = (
    Path(__file__).resolve().parents[3] / "datas" / "geo" / "sigungu_centroids.json"
)
SIGUNGU_FIELD_PATH = (
    Path(__file__).resolve().parents[3]
    / "datas"
    / "data_generator"
    / "시군구 필드.csv"
)


def _load_centroids_json() -> dict[str, tuple[float, float]]:
    if not CENTROIDS_PATH.exists():
        return {}
    data = json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))
    return {name: (v["lat"], v["lon"]) for name, v in data.items()}


def _fallback_coords_from_csv() -> dict[str, tuple[float, float]]:
    """좌표 파일에 없을 때만: 도청 중심 주변 원형 배치."""
    lookup: dict[str, tuple[float, float]] = {}
    if not SIGUNGU_FIELD_PATH.exists():
        return lookup

    df = pd.read_csv(SIGUNGU_FIELD_PATH)
    for province, group in df.groupby("광역지자체 명"):
        center = PROVINCE_CENTERS.get(province, (36.5, 127.5))
        n = len(group)
        for i, row in enumerate(group.itertuples(index=False)):
            name = f"{row[0]} {row[1]}"
            angle = (2 * math.pi * i) / max(n, 1)
            radius = 0.15 + (i % 5) * 0.03
            lat = center[0] + radius * math.cos(angle)
            lon = center[1] + radius * math.sin(angle)
            lookup[name] = (round(lat, 6), round(lon, 6))
    return lookup


def _build_coords_lookup() -> dict[str, tuple[float, float]]:
    global _coords_cache
    if _coords_cache is not None:
        return _coords_cache

    lookup = _load_centroids_json()
    fallback = _fallback_coords_from_csv()
    for name, coords in fallback.items():
        lookup.setdefault(name, coords)

    _coords_cache = lookup
    return lookup


def attach_coordinates(map_df: pd.DataFrame) -> pd.DataFrame:
    lookup = _build_coords_lookup()
    default = (36.5, 127.5)
    result = map_df.copy()
    result["lat"] = result["시군구"].map(lambda s: lookup.get(s, default)[0])
    result["lon"] = result["시군구"].map(lambda s: lookup.get(s, default)[1])
    return result
