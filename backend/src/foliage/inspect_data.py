import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Seattle Combined Tree Point (ArcGIS FeatureServer)
# URL derived from "Combined Tree Point" dataset page
SEATTLE_ARCGIS_URL = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Combined_Tree_Point/FeatureServer/0/query"

def inspect_seattle_arcgis():
    logging.info("Fetching Seattle Combined Tree Point Data Sample...")
    params = {
        "where": "1=1",
        "outFields": "*",
        "resultRecordCount": 5,
        "f": "json"
    }
    try:
        response = requests.get(SEATTLE_ARCGIS_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" in data and len(data["features"]) > 0:
            logging.info("Successfully fetched Seattle ArcGIS data.")
            attributes = data["features"][0]["attributes"]
            logging.info(f"Sample Record Keys: {list(attributes.keys())}")
            logging.info(f"Sample Record: {json.dumps(attributes, indent=2)}")
        else:
            logging.warning("Seattle ArcGIS endpoint returned no features.")
            logging.warning(f"Response: {data}")

    except Exception as e:
        logging.error(f"Failed to fetch Seattle ArcGIS data: {e}")

if __name__ == "__main__":
    inspect_seattle_arcgis()
