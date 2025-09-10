import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests

st.set_page_config(page_title="Jimmy John's Delivery Checker", layout="wide")

st.title("Jimmy John's Delivery Checker")
st.markdown(
    "Enter a Jimmy John's store address to find all establishments in the delivery area. "
    "Results will show directly in the app."
)

# Input for store address
store_address = st.text_input(
    "Enter Jimmy John's store address:",
    "1175 Woods Crossing Rd, Greenville, SC 29607"
)

if st.button("Run Analysis"):
    st.info("Geocoding store address...")
    geolocator = Nominatim(user_agent="jj_delivery_checker")
    location = geolocator.geocode(store_address)

    if location is None:
        st.error("Could not geocode the store address. Check spelling and try again.")
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f"Store coordinates: {lat}, {lon}")

        st.info("Fetching nearby establishments from OpenStreetMap...")
        OVERPASS_QUERY = f"""
        [out:json][timeout:180];
        (
          nwr["shop"](around:4000,{lat},{lon});
          nwr["amenity"](around:4000,{lat},{lon});
          nwr["office"](around:4000,{lat},{lon});
          nwr["healthcare"](around:4000,{lat},{lon});
          nwr["car_dealer"](around:4000,{lat},{lon});
          nwr["building"="apartments"](around:4000,{lat},{lon});
          nwr["building"="residential"](around:4000,{lat},{lon});
        );
        out center;
        """
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": OVERPASS_QUERY}
        )
        data = response.json()

        elements = []
        for el in data["elements"]:
            info = {
                "Name": el.get("tags", {}).get("name", ""),
                "Address": " ".join(filter(None, [
                    el.get("tags", {}).get("addr:housenumber", ""),
                    el.get("tags", {}).get("addr:street", ""),
                    el.get("tags", {}).get("addr:city", "")
                ])),
                "Type": el.get("tags", {}).get("shop") or
                        el.get("tags", {}).get("office") or
                        el.get("tags", {}).get("amenity") or
                        el.get("tags", {}).get("healthcare") or
                        el.get("tags", {}).get("car_dealer") or
                        el.get("tags", {}).get("building", "")
            }
            elements.append(info)

        df = pd.DataFrame(elements)
        st.success(f"Found {len(df)} establishments nearby.")

        # Optional: filter by type
        type_filter = st.multiselect(
            "Filter by type",
            options=df["Type"].dropna().unique().tolist()
        )
        if type_filter:
            df_filtered = df[df["Type"].isin(type_filter)]
            st.dataframe(df_filtered)
        else:
            st.dataframe(df)

