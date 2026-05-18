import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

from services.geo import attach_coordinates


def render_map(map_df, height: int = 520):
    if map_df.empty:
        st.info("지도에 표시할 데이터가 없습니다. 필터 조건을 선택해 주세요.")
        return

    geo_df = attach_coordinates(map_df)
    max_val = geo_df["총_탄소발자국(t_CO2eq)"].max() or 1

    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="OpenStreetMap")
    cluster = MarkerCluster(name="탄소발자국").add_to(m)

    for _, row in geo_df.iterrows():
        value = row["총_탄소발자국(t_CO2eq)"]
        radius = 6 + (value / max_val) * 24
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            popup=folium.Popup(
                f"<b>{row['시군구']}</b><br>{value:,.2f} t CO2eq",
                max_width=280,
            ),
            color="#1a7f4e",
            fill=True,
            fill_color="#2ecc71",
            fill_opacity=0.65,
            weight=1,
        ).add_to(cluster)

    st_folium(m, width=None, height=height, returned_objects=[])
