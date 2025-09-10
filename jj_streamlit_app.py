import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

st.set_page_config(page_title="Jimmy John's Verified Delivery Checker", layout="wide")
st.title("Jimmy John's Verified Delivery Checker")
st.markdown("Enter a Jimmy John's store address. Only addresses **actually deliverable** will be shown.")

store_address = st.text_input(
    "Enter Jimmy John's store address:",
    "1175 Woods Crossing Rd, Greenville, SC 29607"
)

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
    default=["Medical","Food / Restaurants","Retail / Shops","Car / Automotive"]
)

if st.button("Run Verified Analysis"):

    st.info("Geocoding store address...")
    geolocator = Nominatim(user_agent="jj_delivery_checker")
    location = geolocator.geocode(store_address)

    if location is None:
        st.error("Could not geocode store address. Check spelling.")
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
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": OVERPASS_QUERY})
        data = response.json()

        elements = []
        for el in data["elements"]:
            tags = el.get("tags", {})
            if tags.get("healthcare") or tags.get("amenity") in ["hospital","clinic","pharmacy","dentist"]:
                category = "Medical"
            elif tags.get("amenity") in ["restaurant","fast_food","cafe","bar","bakery"]:
                category = "Food / Restaurants"
            elif tags.get("shop") or tags.get("amenity") == "marketplace":
                category = "Retail / Shops"
            elif tags.get("car_dealer") or tags.get("amenity") in ["fuel","car_repair"]:
                category = "Car / Automotive"
            elif tags.get("amenity") in ["school","college","library","kindergarten"]:
                category = "Education / Schools"
            elif tags.get("amenity") in ["cinema","theatre","gym","nightclub","bar"]:
                category = "Entertainment / Leisure"
            elif tags.get("building") in ["apartments","residential"]:
                category = "Residential"
            else:
                category = "Other"

            info = {
                "Name": tags.get("name",""),
                "Address": " ".join(filter(None,[tags.get("addr:housenumber",""),tags.get("addr:street",""),tags.get("addr:city","")])),
                "Category": category
            }
            elements.append(info)

        df = pd.DataFrame(elements)

        st.info("Verifying delivery with Jimmy John's website...")
        verified_addresses = []

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(executable_path="./drivers/chromedriver", options=chrome_options)

        for idx, row in df.iterrows():
            try:
                driver.get("https://www.jimmyjohns.com/order")
                time.sleep(2)
                search_box = driver.find_element(By.ID, "zip-input")
                search_box.clear()
                search_box.send_keys(row["Address"])
                search_box.submit()
                time.sleep(2)
                if "We deliver to" in driver.page_source or "Enter your address" not in driver.page_source:
                    verified_addresses.append(row)
            except Exception:
                continue

        driver.quit()
        df_verified = pd.DataFrame(verified_addresses)
        df_filtered = df_verified[df_verified["Category"].isin(category_filter)]
        st.success(f"Found {len(df_filtered)} verified deliverable establishments.")
        st.dataframe(df_filtered)

        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Verified Results CSV",
            data=csv,
            file_name="jj_verified_delivery.csv",
            mime="text/csv"
        )

