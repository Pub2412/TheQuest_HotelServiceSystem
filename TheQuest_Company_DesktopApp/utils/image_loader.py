"""
Safe image loading and caching utility for Tkinter using Pillow.
Handles relative and absolute paths, aspect-ratio scaling, rounded avatars, and fallbacks.
"""

import os
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CACHE = {}

def get_full_path(rel_or_abs_path: str) -> Path:
    """Resolves path against project root if relative."""
    if not rel_or_abs_path:
        return None
    p = Path(rel_or_abs_path)
    if p.is_absolute() and p.exists():
        return p
    candidate = PROJECT_ROOT / rel_or_abs_path
    if candidate.exists():
        return candidate
    return None

def load_image(
    path_str: str,
    size: tuple,
    preserve_aspect: bool = True,
    circular: bool = False,
    background: tuple = None,
    background_radius: int = 0,
):
    """
    Loads an image from path_str, resizes to size (w, h), and returns ImageTk.PhotoImage.
    If image cannot be loaded, returns a generated placeholder image.
    """
    cache_key = (
        path_str,
        size,
        preserve_aspect,
        circular,
        background,
        background_radius,
    )
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    target_w, target_h = size
    full_path = get_full_path(path_str)

    pil_img = None
    if full_path and full_path.exists():
        try:
            pil_img = Image.open(full_path).convert("RGBA")
        except Exception as e:
            print(f"Warning: could not open image {full_path}: {e}")

    if pil_img is None:
        # Create elegant placeholder
        pil_img = Image.new("RGBA", (target_w, target_h), (59, 24, 95, 255))
        draw = ImageDraw.Draw(pil_img)
        # Draw soft diamond / cross in gold
        draw.rectangle([2, 2, target_w - 3, target_h - 3], outline=(245, 158, 11, 255), width=2)

    if preserve_aspect:
        pil_img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        # Center inside target bounding box
        bg = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        offset_x = (target_w - pil_img.width) // 2
        offset_y = (target_h - pil_img.height) // 2
        bg.paste(pil_img, (offset_x, offset_y), pil_img)
        pil_img = bg
    else:
        pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if background:
        plate = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        plate_draw = ImageDraw.Draw(plate)
        if background_radius:
            plate_draw.rounded_rectangle(
                (0, 0, target_w - 1, target_h - 1),
                radius=background_radius,
                fill=background,
            )
        else:
            plate.paste(Image.new("RGBA", (target_w, target_h), background))
        plate.alpha_composite(pil_img)
        pil_img = plate

    if circular:
        # Create circular mask
        mask = Image.new("L", (target_w, target_h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, target_w, target_h), fill=255)
        output = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        output.paste(pil_img, (0, 0), mask=mask)
        pil_img = output

    photo = ImageTk.PhotoImage(pil_img)
    _CACHE[cache_key] = photo
    return photo

def get_logo_image(size: tuple = (160, 160)):
    """Loads system logo from assets/imgs/logo/logotitle.png."""
    logo_path = "assets/imgs/logo/logotitle.png"
    return load_image(
        logo_path,
        size,
        background=(255, 255, 255, 245),
        background_radius=max(8, min(size) // 10),
    )

def get_icon_logo(size: tuple = (40, 40)):
    """Loads small TQ icon from assets/imgs/logo/logo.png."""
    logo_path = "assets/imgs/logo/logo.png"
    return load_image(
        logo_path,
        size,
        background=(255, 255, 255, 255),
        background_radius=min(size) // 2,
    )

def get_hotel_map_image(max_size: tuple = (1200, 650)):
    """Loads the architectural HotelMap.jpg."""
    map_path = "assets/imgs/HotelMap.jpg"
    return load_image(map_path, max_size, preserve_aspect=True)
