## Разбиение на S2 ячейки по датасету 

```
python3 -m partitioning.create_cells --dataset DATASET --img_min IMG_MIN --img_max IMG_MAX [--output OUTPUT] [--mapping-dir MAPPING_DIR]
```

DATASET - путь к csv-датасету с координатами фотографий (в data/dataset/).

IMG_MIN - минимальное количество фотографий в ячейке.

IMG_MAX - максимальное количество фотографий в ячейке.

OUTPUT - путь к выходной директории.

MAPPING_DIR - путь к mapping директории.
