from fastapi import APIRouter, Response
from PIL import Image
import io
import numpy as np
from .registry import MODEL_REGISTRY, get_model

router = APIRouter()

@router.get("/api/phenology/texture/{symbol}.png")
def get_species_texture(symbol: str):
    """
    Generates a 1x365 pixel texture for the given species.
    X-axis = Day of Year (0-364).
    """
    model = get_model(symbol)
    timeline = model.generate_timeline(365) # List of (R, G, B)

    # Create Image
    # Width 365, Height 1
    # Mode RGB

    # Pack data
    pixels = []
    for c in timeline:
        pixels.extend(c)

    # Using numpy for speed if needed, but simple bytes is fine
    img = Image.new('RGB', (365, 1))
    img.putdata(timeline)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

@router.get("/api/phenology/atlas.png")
def get_atlas():
    """
    Generates a Nx365 texture atlas where each Row is a species.
    Rows are ordered by the keys in MODEL_REGISTRY.
    """
    keys = sorted(MODEL_REGISTRY.keys())
    height = len(keys)
    width = 365

    img = Image.new('RGB', (width, height))

    # Fill rows
    for y, symbol in enumerate(keys):
        model = get_model(symbol)
        timeline = model.generate_timeline(width)

        # Write pixels for this row
        for x, color in enumerate(timeline):
            img.putpixel((x, y), color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

def get_atlas_mapping():
    """Returns {symbol: rowIndex}."""
    keys = sorted(MODEL_REGISTRY.keys())
    return {symbol: i for i, symbol in enumerate(keys)}
