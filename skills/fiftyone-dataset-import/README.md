# Dataset Import

Import any dataset into FiftyOne with automatic format detection. Supports local files, Hugging Face Hub, cloud storage, and multimodal grouped data.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-dataset-import** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server) (optional, recommended for App control)

## Usage

Start the MCP server and ask your AI assistant:

```
"Import the COCO dataset from /path/to/data"
"Load the keremberke/license-plate-object-detection dataset from Hugging Face"
"Import this folder of images, there are cameras and LiDAR files grouped by scene"
```

The skill scans your data, auto-detects the format and media types, and loads the dataset into FiftyOne. It handles images, videos, point clouds, COCO, YOLO, VOC, KITTI, and more without you specifying the format.

## Example

```python
import fiftyone as fo

# After the skill runs, access your dataset
dataset = fo.load_dataset("my-dataset")
print(dataset)
```

## See also

- [Dataset Import docs](https://docs.voxel51.com/user_guide/dataset_creation/index.html)
- [Hugging Face Hub integration](https://docs.voxel51.com/integrations/huggingface.html)
