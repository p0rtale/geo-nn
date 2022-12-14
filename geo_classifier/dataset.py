import os
import re
import json
import random

import torchvision
import torch

import pandas as pd

from pathlib import Path
from typing import Dict, Tuple
from PIL import Image


class PhotoCoordsDataset(torch.utils.data.Dataset):
    def __init__(self, dataset_path, images_dir, transforms):
        self.images_dir = images_dir
        self.transforms = transforms
        self.dataset = pd.read_csv(dataset_path)

    def __len__(self):
        return len(self.dataset * 3)

    def __getitem__(self, idx) -> Tuple[torch.Tensor, dict]:
        subimg_num = idx % 3
        data = self.dataset.iloc[idx // 3]
        img_id, lat, lon, class_label = int(data["img_id"]), data["lat"], data["lon"], int(data["class_label"])

        image = Image.open(os.path.join(self.images_dir, f"image{img_id}.png")).convert("RGB")
        w, h = image.size
        image = image.crop((w // 3 * subimg_num, 0, w // 3 * (subimg_num + 1), h))
        if image.width > 320 and image.height > 320:
            image = torchvision.transforms.Resize(320)(image)
        image = self.transforms(image)

        return image, class_label, lat, lon
