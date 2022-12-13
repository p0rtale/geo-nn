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


class PhotoCoordsCountryDataset(torch.utils.data.Dataset):
    def __init__(self, path: str, transforms):
        self.path = path
        self.transforms = transforms

        with open(os.path.join(self.path, "mapping/map_label_country.json")) as fin:
            self.map_label_country = json.load(fin)

        self.dataset = pd.read_csv(os.path.join(self.path, "datasets/dataset_label.csv"))

    def __len__(self):
        return len(self.dataset * 3)

    def __getitem__(self, idx) -> Tuple[torch.Tensor, dict]:
        subimg_num = idx % 3
        data = self.dataset.iloc[idx // 3]
        img_id, lat, lon, country = int(data["img_id"]), data["lat"], data["lon"], int(data["country"])

        image = Image.open(os.path.join(self.path, f"images/image{img_id}.png")).convert("RGB")
        w, h = image.size
        image = image.crop((w // 3 * subimg_num, 0, w // 3 * (subimg_num + 1), h))
        if image.width > 320 and image.height > 320:
            image = torchvision.transforms.Resize(320)(image)
        image = self.transforms(image)

        return image, country, lat, lon
