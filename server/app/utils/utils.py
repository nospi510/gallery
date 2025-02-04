import os
from PIL import Image

def convert_heic_to_jpeg(heic_path):
    heic_path = heic_path
    jpeg_path = os.path.splitext(heic_path)[0] + '.jpg'
    try:
        with Image.open(heic_path) as img:
            img.convert("RGB").save(jpeg_path, "JPEG")
    except Exception as e:
        print(f"Failed to convert {heic_path} to JPEG: {e}")
