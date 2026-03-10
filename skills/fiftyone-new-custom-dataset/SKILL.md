---
name: fiftyone-new-custom-dataset
description: Create a new FiftyOne custom dataset using user provided path to images and unique dataset name.
compatibility: Requires Python, fiftyone, and all related dependencies
metadata: 
    author: https://github.com/Burhan-Q
    version: 1.0
---
# Create New Custom Dataset

**NOTE**: Presently this is ONLY for image-based datasets.

## Prerequisites

- [ ] `fiftyone` installed
- [ ] unique dataset name
- [ ] full path to dataset image files

### Reference

- Always import `fiftyone` using:
```python
import fiftyone as fo
```

- Fetch supported image formats (use to filter files):
```python
from PIL import Image

IMAGE_FILE_EXTENSIONS = set(Image.registered_extensions().keys())
```

## Steps

1. Ensure `fiftyone` is installed in active Python environment:

```sh
fiftyone --version
```

or using Python

```python
fo.__version__
```

- If not installed, prompt user to either activate virtual environment with `fiftyone` installed, or ask if they would like to install it into the current environment.

2. If no dataset name is provided by the user, you can generate one after first checking the existing dataset names:

```sh
fiftyone datasets list
```

or using Python

```python
fo.list_datasets()
```

When generating a unique dataset name, use the following pattern: `{ADJECTIVE}_{NOUN}_{VERB}`. Some examples (DO NOT USE, THEY ARE ONLY FOR REFERENCE):

    - squiggly_sky_floats
    - droopy_horse_slams
    - smooth_grass_grumbles
    - nervous_hamburger_yodels
    - purple_volcano_drifts
    - spic_telescope_explodes

3. If the user has not provided a path to the images for the dataset, ask the user for the full path to the images.

4. Create the dataset and add the samples.

```python
from pathlib import Path

images_path = Path(USER_PROVIDED_IMAGE_PATH)  # use path provided by user
samples = [
    fo.Sample(filepath=f) 
    for f in images_path.rglob("*") 
    if f.suffix in IMAGE_FILE_EXTENSIONS  # verify file is supported
]
dataset = fo.Dataset(NAME, persistent=True)
dataset.add_samples(samples)
dataset.save()
```