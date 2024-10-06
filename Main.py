from pillow_heif import register_heif_opener
from PIL import Image, ExifTags
import os

register_heif_opener()

image_path = r"XXXXXX"

def print_file_info(path):
    print(f"File path: {path}")
    print(f"File exists: {os.path.exists(path)}")
    print(f"Is file: {os.path.isfile(path)}")
    print(f"File size: {os.path.getsize(path) if os.path.exists(path) else 'N/A'} bytes")

print_file_info(image_path)

try:
    with Image.open(image_path) as img:
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    value = value.decode()
                print(f"{tag}: {value}")
        else:
            print("No EXIF data found in the image.")
except IOError as e:
    print(f"Error opening the image file: {e}")
except Exception as e:
    print(f"Error processing the image EXIF data: {e}")
