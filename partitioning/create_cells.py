import csv
import os
import logging
import sys
import json
import argparse
from time import time
from functools import partial
from multiprocessing import Pool
from collections import Counter, defaultdict

import pandas as pd
import s2sphere as s2


def delete_cells(images_data, cells_image_num, img_min):
    cells_to_del = {k for k, v in cells_image_num.items() if v <= img_min}
    cells_image_num = {k: v for k, v in cells_image_num.items() if v > img_min}
    images_data_new = []
    for data in images_data:
        hexid = data["hexid"]
        if hexid not in cells_to_del:
            images_data_new.append(data)
    return images_data_new, cells_image_num


def create_leaf_cell(lat, lng):
    lat_lng = s2.LatLng.from_degrees(lat, lng)
    cell = s2.Cell.from_lat_lng(lat_lng)
    return cell


def get_parent_hexid(cell, level):
    cell_parent = cell.id().parent(level)
    hexid = cell_parent.to_token()
    return hexid


def init_cells(images_data, level):
    images_data_new = []
    for data in images_data:
        data_new = data
        leaf_cell = create_leaf_cell(lat=data["lat"], lng=data["lon"])
        hexid = get_parent_hexid(leaf_cell, level)
        data_new["leaf_cell"] = leaf_cell
        data_new["hexid"] = hexid
        images_data_new.append(data_new)
    cells_image_num = dict(Counter(data["hexid"] for data in images_data))
    return images_data_new, cells_image_num


def gen_subcells(images_data, cells_image_num, level, img_max):
    images_data_new = []
    cells_image_num_new = {}
    cells_image_num_new = defaultdict(lambda: 0, cells_image_num_new)
    for data in images_data:
        data_new = data
        hexid = data["hexid"]
        if cells_image_num[hexid] > img_max:
            hexid_new = get_parent_hexid(data["leaf_cell"], level)
            data_new["hexid"] = hexid_new
            cells_image_num_new[hexid_new] += 1
        else:
            cells_image_num_new[hexid] += 1
        images_data_new.append(data_new)
    return images_data_new, cells_image_num_new


def write_output(images_data, cells_image_num, map_cell_label, output, filename):
    coords_mean = {}
    for hexid in cells_image_num.keys():
        coords_mean[hexid] = [0, 0]
    for data in images_data:
        coords_mean[data["hexid"]][0] += data["lat"]
        coords_mean[data["hexid"]][1] += data["lon"]

    cells_data = []
    hexids_str = ""
    for hexid, img_num in cells_image_num.items():
        hexids_str += hexid + ","
        cells_data.append({
            "class_label": map_cell_label[hexid],
            "hex_id": hexid,
            "imgs_per_cell": img_num,
            "latitude_mean": coords_mean[hexid][0] / img_num,
            "longitude_mean": coords_mean[hexid][1] / img_num,
        })
    hexids_str = hexids_str[:-1]
    logging.info(f"Hex ids: {hexids_str}.")

    cells_dataset = pd.DataFrame.from_records(cells_data)
    path = os.path.join(output, filename)
    logging.info(f"Write partitioning to {path}")
    cells_dataset.to_csv(path, encoding="utf-8", index=False)


def main(img_min, img_max, output, datasets_dir, dataset_images, labeled_dataset, lvl_min, lvl_max):
    df = pd.read_csv(os.path.join(datasets_dir, dataset_images), usecols=["img_id", "lat", "lon"])
    images_data = df.to_dict('records')
    images_num = len(images_data)
    logging.info(f"{images_num} images available")
    level = lvl_min

    logging.info(f"Initialize cells of level {level}")
    images_data, cells_image_num = init_cells(images_data, level)
    logging.info(f"Number of classes: {len(cells_image_num)}")

    logging.info("Remove cells with image_num < img_min")
    images_data, cells_image_num = delete_cells(images_data, cells_image_num, img_min)
    logging.info(f"Number of classes: {len(cells_image_num)}")

    logging.info("Create subcells")
    while any(v > img_max for v in cells_image_num.values()) and level < lvl_max:
        level = level + 1
        logging.info(f"Level {level}.")
        images_data, cells_image_num = gen_subcells(images_data, cells_image_num, level, img_max)
        logging.info(f"Number of classes: {len(cells_image_num)}")

    logging.info("Remove cells with image_num < img_min")
    images_data, cells_image_num = delete_cells(images_data, cells_image_num, img_min)
    logging.info(f"Number of classes: {len(cells_image_num)}")
    logging.info(f"Number of images: {len(images_data)}")

    map_cell_label = {}
    label = 0
    for hexid in cells_image_num.keys():
        map_cell_label[hexid] = label
        label += 1

    labeled_data = []
    for data in images_data:
        labeled_data.append({
            "img_id": data["img_id"],
            "lat": data["lat"],
            "lon": data["lon"],
            "class_label": map_cell_label[data["hexid"]],
        })
    labeled_df = pd.DataFrame.from_records(labeled_data)
    path = os.path.join(datasets_dir, labeled_dataset)
    logging.info(f"Write labeled dataset to {path}")
    labeled_df.to_csv(path, encoding="utf-8", index=False)

    write_output(
        images_data,
        cells_image_num,
        map_cell_label,
        output,
        filename=f"cells_{img_min}_{img_max}_images_{images_num}.csv",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--img-min", dest="img_min", type=int, required=True)
    parser.add_argument("--img-max", dest="img_max", type=int, required=True)
    parser.add_argument("--output", type=str, default="partitioning/output")
    parser.add_argument("--datasets-dir", dest="datasets_dir", type=str, default="data/datasets")
    parser.add_argument("--dataset-images", dest="dataset_images", type=str, default="dataset_images.csv")
    parser.add_argument("--labeled-dataset", dest="labeled_dataset", type=str, default="dataset_label_cell.csv")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    level = logging.INFO
    logging.basicConfig(level=level)

    main(
        img_min=args.img_min,
        img_max=args.img_max,
        output=args.output,
        datasets_dir=args.datasets_dir,
        dataset_images=args.dataset_images,
        labeled_dataset=args.labeled_dataset,
        lvl_min=2,
        lvl_max=30,
    )
