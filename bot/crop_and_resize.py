import os
import argparse
from PIL import Image


def concat_images(images):
    widths, heights = zip(*(img.size for img in images))
    total_width = sum(widths)
    max_height = max(heights)

    image_new = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for img in images:
        image_new.paste(img, (x_offset, 0))
        x_offset += img.size[0]

    return image_new


def transform_image(image, height):
    w, h = image.size
    left = 0.075
    right = 0.18
    bottom = 0.07
    image_new = image.crop((w * left, 0, w * (1 - right), h * (1 - bottom)))

    w_new = 900
    h_new = height
    image_new.thumbnail((w_new, h_new))

    return image_new


def get_panorama(input_dir, output_dir, n_from, n_to, height, clear):
    for i in range(n_from, n_to + 1):
        images = []
        for j in range(3):
            image = Image.open(os.path.join(input_dir, f'image{i}_{j}.png'))
            if clear:
                os.remove(os.path.join(input_dir, f'image{i}_{j}.png'))
            image_transformed = transform_image(image, height)
            images.append(image_transformed)
        image_panorama = concat_images(images)
        image_panorama.save(os.path.join(output_dir, f'image{i}.png'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", dest="input_dir", required=True, type=str)
    parser.add_argument("--output-dir", dest="output_dir", required=True, type=str)
    parser.add_argument("--n-from", dest="n_from", required=True, type=int)
    parser.add_argument("--n-to", dest="n_to", required=True, type=int)
    parser.add_argument("--height", dest="height", required=True, type=int)
    parser.add_argument("--clear", dest="clear", action="store_true")
    args = parser.parse_args()

    get_panorama(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        n_from=args.n_from,
        n_to=args.n_to,
        height=args.height,
        clear=args.clear
    )
