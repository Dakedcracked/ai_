from typing import Tuple, Optional
import io

from PIL import Image

try:
    import pydicom
    _HAVE_PYDICOM = True
except Exception:
    _HAVE_PYDICOM = False


def load_image_from_bytes(data: bytes, filename: str) -> Tuple[Image.Image, str]:
    """Load image from raw bytes, handling common formats and DICOM if available.

    Returns a PIL.Image and modality string.
    """
    name = filename.lower()
    if name.endswith(".dcm") and _HAVE_PYDICOM:
        ds = pydicom.dcmread(io.BytesIO(data))  # type: ignore
        arr = ds.pixel_array  # type: ignore
        # Normalize to 0-255
        arr_min, arr_max = arr.min(), arr.max()
        if arr_max > arr_min:
            arr = (arr - arr_min) * (255.0 / (arr_max - arr_min))
        img = Image.fromarray(arr.astype("uint8"))
        return img, getattr(ds, "Modality", "DICOM")

    # Fall back to PIL for images
    img = Image.open(io.BytesIO(data)).convert("RGB")
    modality = "CT" if name.endswith((".png", ".jpg", ".jpeg")) else "Unknown"
    return img, modality
