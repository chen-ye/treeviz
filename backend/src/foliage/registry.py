from .models import DeciduousModel, FloweringModel

# Registry of models per USDA symbol
# Ideally loaded from DB or JSON, but hardcoded for prototype speed
MODEL_REGISTRY = {
    "ACPL": DeciduousModel(peak_color=(255, 165, 0)), # Norway Maple (Orange)
    "ACRU": DeciduousModel(peak_color=(220, 20, 60), fall_start=265), # Red Maple (Red)
    "PRCE2": FloweringModel(flower_color=(255, 182, 193), flower_start=70, flower_end=90, peak_color=(178, 34, 34)), # Cherry Plum
    "PRSE3": FloweringModel(flower_color=(255, 105, 180), flower_start=90, flower_end=110, peak_color=(255, 140, 0)), # Kwanzan Cherry
    "DEFAULT": DeciduousModel()
}

def get_model(symbol: str):
    return MODEL_REGISTRY.get(symbol, MODEL_REGISTRY["DEFAULT"])
