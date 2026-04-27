"""Entry points for the remote zoo source. Manifest top-level `name` is required."""

# framework-first: relative import keeps the worker-pickle path resolvable
from .zoo import YourModel


def download_model(model_name: str, model_path: str) -> None:
    """Download weights to model_path. Must be idempotent."""
    raise NotImplementedError


def load_model(
    model_name: str | None = None,
    model_path: str | None = None,
    **kwargs,
) -> "fiftyone.core.models.Model":
    """Return a model instance, not a config."""
    return YourModel(model_name=model_name, model_path=model_path, **kwargs)


# Optional: implement only if the model is invoked from an operator UI.
# def resolve_input(model_name: str, ctx) -> "fiftyone.operators.types.Property | None":
#     return None
