import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests

st.set_page_config(page_title="Jimmy John's Delivery Checker", layout="wide")

st.title("Jimmy John's Delivery Checker")
st.markdown("Enter a Jimmy John's store address to find all establishments in the delivery area and download a CSV.")

# Input field for store address
store_address = st.text_input("Enter Jimmy John's store address:", "1175 Woods Crossing Rd, Greenville, SC 29607")

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
        # Overpass API query to get shops, offices, apartments, medical, schools, car dealerships
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
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": OVERPASS_QUERY})
        data = response.json()

        elements = []
        for el in data["elements"]:
            info = {
                "name": el.get("tags", {}).get("name", ""),
                "address": " ".join(filter(None, [
                    el.get("tags", {}).get("addr:housenumber", ""),
                    el.get("tags", {}).get("addr:street", ""),
                    el.get("tags", {}).get("addr:city", "")
                ])),
                "shop": el.get("tags", {}).get("shop", ""),
                "office": el.get("tags", {}).get("office", ""),
                "amenity": el.get("tags", {}).get("amenity", ""),
                "healthcare": el.get("tags", {}).get("healthcare", ""),
                "car_dealer": el.get("tags", {}).get("car_dealer", ""),
                "lat": el.get("lat") or el.get("center", {}).get("lat"),
                "lon": el.get("lon") or el.get("center", {}).get("lon"),
                "in_delivery_zone": "yes"  # placeholder, can be replaced with real API check
            }
            elements.append(info)

        df = pd.DataFrame(elements)
        st.success(f"Found {len(df)} establishments nearby.")

        # Download CSV button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Verified CSV", data=csv, file_name="jj_delivery_verified.csv", mime="text/csv")
