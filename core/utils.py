from PIL import Image
import os

def convert_to_ico(src_img, dst_ico):
    img = Image.open(src_img)
    img.save(dst_ico, format="ICO")

def is_valid_path(path):
    return os.path.exists(path) 