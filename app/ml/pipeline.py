from typing import Any, Dict


class MLPipeline:
    """Placeholder ML pipeline for credit risk prediction.

    This class is intentionally minimal: it defines a stable public API
    that downstream code can call. Implementations should subclass or
    replace methods as model artifacts become available.
    """

    def __init__(self) -> None:
        self.model = None

    def load(self, path: str) -> None:
        """Load model artifacts from `path` (not implemented)."""
        raise NotImplementedError("Model loading not implemented")

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Return a deterministic placeholder prediction.

        Returns a mapping with a numeric `score` in [0,1] and a
        string `label`. This ensures stable response format for clients.
        """
        return {"score": 0.5, "label": "unknown"}
