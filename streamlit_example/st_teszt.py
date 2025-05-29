# -*- coding: utf-8 -*-
"""
Created on Wed May 28 10:42:18 2025

@author: B0898
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

# Alapértelmezett térkép középpont
m = folium.Map(location=[47.5, 19.0], zoom_start=7)

# WMS réteg hozzáadása
folium.raster_layers.WmsTileLayer(
    url='http://127.0.0.1:5000/wms',
    name='Túraut',
    layers='all',  # Cseréld ki a saját rétegnevedre
    fmt='image/png',
    transparent=True,
    version='1.1.1',
    attr='Saját WMS',
    overlay=True,
    control=True
).add_to(m)

# Rétegvezérlő hozzáadása
folium.LayerControl().add_to(m)

# Térkép megjelenítése Streamlit-ben
st.title("WMS megjelenítés Streamlit + Folium segítségével")
st_folium(m, width=800, height=600)