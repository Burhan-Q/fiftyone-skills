# zoo.py — Class Hierarchy

## Use these, don't replace these

**Framework-first**: FiftyOne already provides the pickle-safe primitives. Subclassing or overriding these re-introduces the **Worker-pickle constraint** failures (see DATALOADER.md).

| Concern | Use this | Do NOT |
|---------|----------|--------|
| Batch collation | `TorchModelMixin.collate_fn` (inherited) | Override `collate_fn` |
| Dataset item loading | `fiftyone.utils.torch.ImageGetItem(raw_inputs=True)` | Subclass `GetItem` |
| `transforms` / `preprocess` / `ragged_batches` / `needs_fields` / `has_collate_fn` | Implement on your model class | These are the seams — implement, don't avoid |

## Config

```python
import fiftyone.utils.torch as fout

class MyModelConfig(fout.TorchImageModelConfig):
    def __init__(self, d: dict):
        if "raw_inputs" not in d:
            d["raw_inputs"] = True
        super().__init__(d)
        self.model_path = self.parse_string(d, "model_path", default="org/model")
```

## Model — multi-inheritance order matters

```python
import fiftyone.core.models as fom
from fiftyone.core.models import SupportsGetItem, TorchModelMixin
from fiftyone.utils.torch import ImageGetItem

class MyBaseModel(fom.Model, fom.SamplesMixin, SupportsGetItem, TorchModelMixin):
    def __init__(self, config):
        fom.SamplesMixin.__init__(self)
        SupportsGetItem.__init__(self)
        self._preprocess = False
        self.config = config

    @property
    def transforms(self): return None

    @property
    def preprocess(self) -> bool: return self._preprocess
    @preprocess.setter
    def preprocess(self, value: bool): self._preprocess = value

    @property
    def ragged_batches(self) -> bool: return False

    @property
    def needs_fields(self) -> dict: return self._fields
    @needs_fields.setter
    def needs_fields(self, fields: dict): self._fields = fields

    @property
    def has_collate_fn(self) -> bool: return True

    def build_get_item(self, field_mapping=None) -> ImageGetItem:
        return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)
```

## predict / predict_all — input dispatch

**FiftyOne always passes `PIL.Image` to `predict_all`** when the model inherits `SupportsGetItem` and/or `TorchModelMixin`. Every framework call site loads the image before calling the model:

| Framework path | Source of input | Where (`fiftyone/core/models.py`) |
|---|---|---|
| `_apply_image_model_data_loader` (DataLoader) | `ImageGetItem(raw_inputs=True)` → `PIL.Image` | dispatch lines 184–191; call lines 498–502 |
| `_apply_image_model_single` (fallback) | `foui.read(sample.filepath)` → `PIL.Image` | line 372, then `model.predict(img)` line 375 |
| `_apply_image_model_batch` (fallback batch) | `foui.read(...)` → list of `PIL.Image` | line 417, then `model.predict_all(imgs)` line 420 |
| `_apply_image_model_to_frames_*` (video frames) | numpy frame array from `FFmpegVideoReader` | line 566, line 672 |

The `Model.predict_all` contract (`fiftyone/core/models.py:2365`) lists "uint8 numpy arrays (HWC) or numpy array tensors (NHWC)". `TorchImageModel.predict_all` (`fiftyone/utils/torch.py:873`) lists "PIL images, uint8 numpy arrays, Torch tensors". Neither mentions `str`. A structural search across `fiftyone/utils/*.py` finds **zero** `isinstance(_, str)` dispatch inside any `predict` / `predict_all` — no first-party model accepts a filepath string.

**Implication:** the template only needs the `PIL.Image` branch. A `str` (filepath) branch is dead code — `dataset.apply_model` never produces it and no first-party model contract supports it.

For non-VLM models the body is trivial — accept the image directly:

```python
def predict(self, arg, sample=None):
    return self.predict_all([arg], samples=[sample] if sample else None)[0]

def predict_all(self, batch, samples=None):
    return [self._run_inference(image) for image in batch]
```

**VLM exception — optional `dict` input.** For VLMs you often want per-item prompts. `apply_model` does not produce dicts either (the DataLoader still yields `PIL.Image`), so a dict shape is purely a *direct-invocation convenience* for users calling `model.predict({"image": img, "prompt": "..."})` outside the framework. If you want to expose that, branch on `isinstance(item, dict)` and fall through otherwise:

```python
def predict_all(self, batch, samples=None):
    results = []
    for i, item in enumerate(batch):
        sample = samples[i] if samples and i < len(samples) else None
        if isinstance(item, dict):
            image = item.get("image") or item.get("filepath")
            prompt = item.get("prompt")
        else:
            image, prompt = item, None     # PIL.Image (DataLoader path)

        if prompt is None and sample and "prompt_field" in self._fields:
            fn = self._fields["prompt_field"]
            if sample.has_field(fn):
                prompt = sample.get_field(fn)
        prompt = prompt or self.config.prompt
        results.append(self._run_inference(image, prompt))
    return results
```

If you don't want the dict convenience, drop the `isinstance` check entirely and assume `PIL.Image`.
