import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests

st.set_page_config(page_title="Jimmy John's Delivery Checker", layout="wide")

st.title("Jimmy John's Delivery Checker")
st.markdown(
    "Enter a Jimmy John's store address to find establishments in the delivery area. "
    "Filter by broad categories and download the results if needed."
)

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
            tags = el.get("tags", {})

            # Broad categories
            if tags.get("healthcare") or tags.get("amenity") in ["hospital", "clinic", "pharmacy", "dentist"]:
                category = "Medical"
            elif tags.get("amenity") in ["restaurant", "fast_food", "cafe", "bar", "bakery"]:
                category = "Food / Restaurants"
            elif tags.get("shop") or tags.get("amenity") in ["marketplace"]:
                category = "Retail / Shops"
            elif tags.get("car_dealer") or tags.get("amenity") in ["fuel", "car_repair"]:
                category = "Car / Automotive"
            elif tags.get("amenity") in ["school", "college", "library", "kindergarten"]:
                category = "Education / Schools"
            elif tags.get("amenity") in ["cinema", "theatre", "gym", "nightclub", "bar"]:
                category = "Entertainment / Leisure"
            elif tags.get("building") in ["apartments", "residential"]:
                category = "Residential"
            else:
                category = "Other"

            info = {
                "Name": tags.get("name", ""),
                "Address": " ".join(filter(None, [
                    tags.get("addr:housenumber", ""),
                    tags.get("addr:street", ""),
                    tags.get("addr:city", "")
                ])),
                "Category": category
            }
            elements.append(info)

        df = pd.DataFrame(elements)
        st.success(f"Found {len(df)} establishments nearby.")

        # Filter by category
        category_filter = st.multiselect(
            "Filter by Category",
            options=[
                "Medical",
                "Food / Restaurants",
                "Retail / Shops",
                "Car / Automotive",
                "Education / Schools",
                "Entertainment / Leisure",
                "Residential",
                "Other"
            ],
            default=[
                "Medical",
                "Food / Restaurants",
                "Retail / Shops",
                "Car / Automotive"
            ]
        )
        df_filtered = df[df["Category"].isin(category_filter)]
        st.dataframe(df_filtered)

        # Download CSV
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Filtered Results as CSV",
            data=csv,
            file_name="jj_delivery_establishments.csv",
            mime="text/csv"
        )


