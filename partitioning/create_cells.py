import csv
import os
import logging
import sys
import json
import argparse
from time import time
from functools import partial
from multiprocessing import Pool
from collections import Counter

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
    for data in images_data:
        data_new = data
        hexid = data["hexid"]
        if cells_image_num[hexid] > img_max:
            hexid_new = get_parent_hexid(data["leaf_cell"], level)
            data_new["hexid"] = hexid_new
            try:
                cells_image_num_new[hexid_new] += 1
            except:
                cells_image_num_new[hexid_new] = 1
        else:
            try:
                cells_image_num_new[hexid] += 1
            except:
                cells_image_num_new[hexid] = 1
        images_data_new.append(data_new)
    return images_data_new, cells_image_num_new


def write_output(images_data, cells_image_num, images_num, img_min, img_max, output, mapping_dir):
    if not os.path.exists(output):
        os.makedirs(output)

    filename = f"cells_{img_min}_{img_max}_images_{images_num}.csv"
    logging.info(f"Write partitioning to {os.path.join(output, filename)}")
    with open(os.path.join(output, filename), "w") as fout:
        cells_writer = csv.writer(fout, delimiter=",")

        cells_writer.writerow(
            [
                "class_label",
                "hex_id",
                "imgs_per_cell",
                "latitude_mean",
                "longitude_mean",
            ]
        )

        map_cell_label = {}
        coords_mean = {}
        label = 0
        for hexid in cells_image_num.keys():
            map_cell_label[hexid] = label
            coords_mean[hexid] = [0, 0]
            label += 1

        map_image_label = {}
        for data in images_data:
            map_image_label[data["img_id"]] = map_cell_label[data["hexid"]]
            coords_mean[data["hexid"]][0] += data["lat"]
            coords_mean[data["hexid"]][1] += data["lon"]

        map_path = os.path.join(mapping_dir, "map_label_cell.json")
        logging.info(f"Write label mapping to {map_path}")
        with open(map_path, "w") as fout:
            json.dump(map_image_label, fout)

        hexids_str = ""
        for hexid, img_num in cells_image_num.items():
            hexids_str += hexid + ","
            cells_writer.writerow(
                [
                    map_cell_label[hexid],
                    hexid,
                    img_num,
                    coords_mean[hexid][0] / img_num,
                    coords_mean[hexid][1] / img_num
                ]
            )
        hexids_str = hexids_str[:-1]
        logging.info(f"Hex ids: {hexids_str}.")


def main(dataset, output, mapping_dir, img_min, img_max, lvl_min, lvl_max):
    df = pd.read_csv(dataset, usecols=["img_id", "lat", "lon"])
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

    logging.info("Write output file")
    write_output(images_data, cells_image_num, images_num, img_min, img_max, output, mapping_dir)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--img-min", dest="img_min", type=int, required=True)
    parser.add_argument("--img-max", dest="img_max", type=int, required=True)
    parser.add_argument("--output", type=str, default="partitioning/output")
    parser.add_argument("--mapping-dir", dest="mapping_dir", type=str, default="data/mapping")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    level = logging.INFO
    logging.basicConfig(level=level)

    main(
        dataset=args.dataset,
        output=args.output,
        mapping_dir=args.mapping_dir,
        img_min=args.img_min,
        img_max=args.img_max,
        lvl_min=2,
        lvl_max=30,
    )
