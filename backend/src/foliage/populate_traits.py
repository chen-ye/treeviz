import json
import os

def populate_traits():
    # Paths
    base_dir = os.path.dirname(__file__)
    top_50_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "top_50_species.json")
    traits_path = os.path.join(base_dir, "phenology_traits.json")

    # Load Top 50
    if not os.path.exists(top_50_path):
        print(f"Error: {top_50_path} not found.")
        return

    with open(top_50_path, "r") as f:
        top_50 = json.load(f)

    # Load existing traits or start fresh
    traits = {}
    if os.path.exists(traits_path):
        with open(traits_path, "r") as f:
            traits = json.load(f)

    # Heuristics
    # Colors: R, G, B
    COLORS = {
        "red": [220, 20, 60],
        "orange": [255, 165, 0],
        "yellow": [255, 215, 0],
        "brown": [139, 69, 19],
        "pink": [255, 192, 203],
        "white": [255, 255, 255],
        "evergreen": [34, 139, 34]
    }

    # Genus mappings
    GENUS_MAP = {
        "acer": {"type": "Deciduous", "peak_color": COLORS["red"]}, # Maples
        "prunus": {"type": "Flowering", "flower_color": COLORS["pink"], "peak_color": COLORS["orange"]}, # Cherries/Plums
        "liquidambar": {"type": "Deciduous", "peak_color": COLORS["orange"]}, # Sweetgum
        "crataegus": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["orange"]}, # Hawthorn
        "pyrus": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["red"]}, # Pear
        "betula": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Birch
        "tilia": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Linden
        "quercus": {"type": "Deciduous", "peak_color": COLORS["brown"]}, # Oak
        "gleditsia": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Honeylocust
        "carpinus": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Hornbeam
        "cornus": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["red"]}, # Dogwood
        "pseudotsuga": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Douglas-fir
        "fraxinus": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Ash
        "thuja": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Cedar/Arborvitae
        "zelkova": {"type": "Deciduous", "peak_color": COLORS["orange"]}, # Zelkova
        "liriodendron": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Tuliptree
        "cercidiphyllum": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Katsura
        "aesculus": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["yellow"]}, # Horse Chestnut
        "sorbus": {"type": "Deciduous", "peak_color": COLORS["orange"]}, # Mountain Ash
        "styrax": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["yellow"]}, # Snowbell
        "ulmus": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Elm
        "magnolia": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["brown"]}, # Magnolia
        "ginkgo": {"type": "Deciduous", "peak_color": COLORS["yellow"]}, # Ginkgo
        "tsuga": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Hemlock
        "chamaecyparis": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Cypress
        "robinia": {"type": "Flowering", "flower_color": COLORS["white"], "peak_color": COLORS["yellow"]}, # Locust
        "ilex": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Holly
        "picea": {"type": "Evergreen", "peak_color": COLORS["evergreen"]}, # Spruce
        "cercis": {"type": "Flowering", "flower_color": COLORS["pink"], "peak_color": COLORS["yellow"]}, # Redbud
        "fagus": {"type": "Deciduous", "peak_color": COLORS["brown"]}, # Beech
    }

    count_new = 0
    count_updated = 0

    for item in top_50:
        symbol = item["symbol"]
        if not symbol:
            continue

        scientific_name = item["scientific_name"].lower()
        genus = scientific_name.split(" ")[0] if scientific_name != "n/a" else ""

        if symbol in traits:
            # Skip if already exists? Or update? Let's update if we have better info
            # For now, just skip to preserve manual edits unless it's a new run
            pass

        # Determine traits
        mapping = GENUS_MAP.get(genus, {"type": "Deciduous", "peak_color": COLORS["yellow"]}) # Default to yellow deciduous

        # Construct trait object
        trait_entry = {
            "common_name": item["common_name"],
            "type": mapping["type"],
            "peak_color": mapping["peak_color"]
        }

        if mapping["type"] == "Deciduous":
            trait_entry.update({
                "fall_start_doy": 280,
                "fall_peak_doy": 305,
                "fall_end_doy": 330
            })
        elif mapping["type"] == "Flowering":
            trait_entry.update({
                "flower_color": mapping.get("flower_color", COLORS["white"]),
                "flower_start": 80,
                "flower_end": 100,
                "fall_start_doy": 280,
                "fall_peak_doy": 305,
                "fall_end_doy": 330
            })
        # Evergreen needs no extra fields for now

        traits[symbol] = trait_entry
        count_new += 1

    # Write back
    with open(traits_path, "w") as f:
        json.dump(traits, f, indent=2)

    print(f"Updated phenology traits. Total species: {len(traits)}")

if __name__ == "__main__":
    populate_traits()
