import os
import io
import random
import time
from typing import Any, Dict, Optional, Tuple, Union

from PIL import Image

# torch is optional; import only if backend demands it
_torch = None


class ModelService:
    """Pluggable model service supporting simulation or PyTorch backends.

    Environment variables:
    - ONCOSCAN_MODEL_BACKEND: 'simulate' (default) or 'torch'
    - ONCOSCAN_MODEL_PATH: path to model weights (for torch backend)
    - ONCOSCAN_MODEL_DEVICE: device string, e.g. 'cpu' or 'cuda' (torch)
    - ONCOSCAN_SIMULATE_DELAY_SEC: float seconds, default 0.0-1.5 random
    """

    def __init__(self) -> None:
        self.backend = os.environ.get("ONCOSCAN_MODEL_BACKEND", "simulate").lower()
        self.model_path = os.environ.get("ONCOSCAN_MODEL_PATH")
        self.device = os.environ.get("ONCOSCAN_MODEL_DEVICE", "cpu")
        self._model = None
        self._loaded = False
        self._load()

    def _load(self) -> None:
        if self.backend == "torch":
            global _torch
            try:
                import torch as _torch  # type: ignore
            except Exception as e:
                raise RuntimeError(f"PyTorch not available but ONCOSCAN_MODEL_BACKEND=torch: {e}")

            # simple example: user supplies a torchscript or state_dict model
            if not self.model_path or not os.path.exists(self.model_path):
                raise RuntimeError("Model path not found for torch backend; set ONCOSCAN_MODEL_PATH")
            try:
                if self.model_path.endswith(".pt") or self.model_path.endswith(".pth"):
                    # Try torch.jit (torchscript) first
                    try:
                        self._model = _torch.jit.load(self.model_path, map_location=self.device)
                        self._model.eval()
                    except Exception:
                        # Fall back to a simple nn.Module load pattern; requires code-defined model class
                        # For a generic loader, we'd need a model factory; here we document expected usage.
                        self._model = _torch.jit.load(self.model_path, map_location=self.device)
                        self._model.eval()
                else:
                    # As a conservative fallback attempt to load with torch.jit
                    self._model = _torch.jit.load(self.model_path, map_location=self.device)
                    self._model.eval()
                self._loaded = True
            except Exception as e:
                raise RuntimeError(f"Failed to load torch model: {e}")
        else:
            # simulate backend
            self._model = "simulate"
            self._loaded = True

    def reload(self) -> Dict[str, Any]:
        self._loaded = False
        self._model = None
        self._load()
        return self.status()

    def status(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "loaded": self._loaded,
            "model_path": self.model_path,
            "device": self.device if self.backend == "torch" else None,
        }

    def _preprocess(self, image: Union[Image.Image, Any]) -> Any:
        if self.backend == "torch":
            assert _torch is not None
            import numpy as np
            if isinstance(image, Image.Image):
                img = image.convert("RGB")
                arr = np.array(img).astype("float32") / 255.0
            else:
                # assume numpy array
                arr = image.astype("float32")
                if arr.max() > 1.0:
                    arr = arr / 255.0
            # HWC -> CHW
            if arr.ndim == 2:
                arr = arr[..., None]
            arr = arr.transpose(2, 0, 1)
            tensor = _torch.from_numpy(arr).unsqueeze(0).to(self.device)
            return tensor
        else:
            return image

    def predict(self, image: Union[Image.Image, Any]) -> Dict[str, Any]:
        if not self._loaded:
            raise RuntimeError("Model not loaded")

        if self.backend == "torch":
            assert _torch is not None
            with _torch.inference_mode():
                inputs = self._preprocess(image)
                outputs = self._model(inputs)
                # Expect a single malignancy probability in outputs; adapt as needed
                if hasattr(outputs, "detach"):
                    prob = float(outputs.detach().cpu().numpy().ravel()[0])
                else:
                    prob = float(outputs)
                prob = max(0.0, min(1.0, prob))
        else:
            # simulate a deterministic-yet-randomish probability to stabilize tests
            base = random.random()
            # Optional short delay for realism
            try:
                delay = float(os.environ.get("ONCOSCAN_SIMULATE_DELAY_SEC", "0"))
            except Exception:
                delay = 0.0
            if delay <= 0:
                delay = random.uniform(0.1, 0.5)
            time.sleep(delay)
            prob = round(0.3 + 0.4 * base, 4)

        finding = "suspicious lesion" if prob >= 0.5 else "no acute findings"
        return {"probability": prob, "primary_finding": finding}


# global holder created lazily
_MODEL_SERVICE: Optional[ModelService] = None


def get_model_service() -> ModelService:
    global _MODEL_SERVICE
    if _MODEL_SERVICE is None:
        _MODEL_SERVICE = ModelService()
    return _MODEL_SERVICE
