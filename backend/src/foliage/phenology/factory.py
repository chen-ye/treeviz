"""Factory for creating tree phenology models."""
from .base import TreePhenologyModel
from .species.cherry_plum import CherryPlum
from .species.norway_maple import NorwayMaple
from .species.sweetgum import Sweetgum
from .species.red_oak import NorthernRedOak
from .species.douglas_fir import DouglasFir
# New Species
from .species.smooth_hawthorn import SmoothHawthorn
from .species.callery_pear import CalleryPear
from .species.european_white_birch import EuropeanWhiteBirch
from .species.japanese_maple import JapaneseMaple
from .species.littleleaf_linden import LittleleafLinden
from .species.japanese_flowering_cherry import JapaneseFloweringCherry
from .species.honeylocust import Honeylocust
from .species.european_hornbeam import EuropeanHornbeam
from .species.flowering_dogwood import FloweringDogwood
from .species.oregon_ash import OregonAsh

# Map USDA symbols (or common names) to model classes
# In a real app, this might be loaded from a config or DB
MODEL_REGISTRY = {
    # Original 5
    'ACPL': NorwayMaple,
    'ACRU': NorwayMaple, # Proxy
    'LIST2': Sweetgum,
    'QURU': NorthernRedOak,
    'PSME': DouglasFir,
    'PRCE': CherryPlum,

    # New 10
    'CRLA80': SmoothHawthorn,
    'PYCA80': CalleryPear,
    'BEPE3': EuropeanWhiteBirch,
    'ACPA2': JapaneseMaple,
    'TICO2': LittleleafLinden,
    'PRSE3': JapaneseFloweringCherry,
    'GLTR': Honeylocust,
    'CABE8': EuropeanHornbeam,
    'COFL2': FloweringDogwood,
    'FRLA': OregonAsh,

    # Common Name Fallbacks
    'cherry_plum': CherryPlum,
    'norway_maple': NorwayMaple,
    'sweetgum': Sweetgum,
    'red_oak': NorthernRedOak,
    'douglas_fir': DouglasFir,
    'smooth_hawthorn': SmoothHawthorn,
    'callery_pear': CalleryPear,
    'european_white_birch': EuropeanWhiteBirch,
    'japanese_maple': JapaneseMaple,
    'littleleaf_linden': LittleleafLinden,
    'japanese_flowering_cherry': JapaneseFloweringCherry,
    'honeylocust': Honeylocust,
    'european_hornbeam': EuropeanHornbeam,
    'flowering_dogwood': FloweringDogwood,
    'oregon_ash': OregonAsh,
}

def get_model_for_species(usda_symbol: str) -> type[TreePhenologyModel]:
    """
    Get the model class for a given species symbol.
    Returns a default model (NorwayMaple) if not found.
    """
    return MODEL_REGISTRY.get(usda_symbol, NorwayMaple)
