from .models import DeciduousModel, FloweringModel, EvergreenModel
import json
import os
import logging

# Registry of models per USDA symbol
MODEL_REGISTRY = {}

def load_registry():
    global MODEL_REGISTRY
    try:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "phenology_traits.json")

        if not os.path.exists(path):
            logging.warning(f"Phenology traits file not found at {path}")
            return

        with open(path, "r") as f:
            traits = json.load(f)

        for symbol, data in traits.items():
            model_type = data.get("type", "Deciduous")

            if model_type == "Evergreen":
                MODEL_REGISTRY[symbol] = EvergreenModel(
                    color=tuple(data.get("peak_color", [34, 139, 34]))
                )
            elif model_type == "Flowering":
                MODEL_REGISTRY[symbol] = FloweringModel(
                    flower_color=tuple(data.get("flower_color", [255, 192, 203])),
                    flower_start=data.get("flower_start", 80),
                    flower_end=data.get("flower_end", 100),
                    peak_color=tuple(data.get("peak_color", [255, 165, 0])),
                    fall_start=data.get("fall_start_doy", 280),
                    fall_peak=data.get("fall_peak_doy", 305),
                    fall_end=data.get("fall_end_doy", 330)
                )
            else: # Deciduous
                MODEL_REGISTRY[symbol] = DeciduousModel(
                    peak_color=tuple(data.get("peak_color", [255, 165, 0])),
                    fall_start=data.get("fall_start_doy", 280),
                    fall_peak=data.get("fall_peak_doy", 305),
                    fall_end=data.get("fall_end_doy", 330)
                )

        # Add default if not present
        if "DEFAULT" not in MODEL_REGISTRY:
             MODEL_REGISTRY["DEFAULT"] = DeciduousModel()

    except Exception as e:
        logging.error(f"Failed to load phenology registry: {e}")
        # Fallback
        MODEL_REGISTRY["DEFAULT"] = DeciduousModel()

# Load on import
load_registry()

def get_model(symbol: str):
    return MODEL_REGISTRY.get(symbol, MODEL_REGISTRY.get("DEFAULT"))
