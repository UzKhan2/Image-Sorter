import os
import piexif
from PIL import Image, ExifTags, UnidentifiedImageError
import pillow_heif
import requests
import shutil
import exiftool
from datetime import datetime
from constants import IMAGE_FORMATS, VIDEO_FORMATS

def print_file_info(path):
    file_name = os.path.basename(path)
    file_size = os.path.getsize(path)
    print(f"File: {file_name}")
    print(f"Size: {file_size} bytes")

def extract_gps_info_image(file_path):
    pillow_heif.register_heif_opener()
    
    print_file_info(file_path)
    
    try:
        with Image.open(file_path) as img:
            print(f"Format: {img.format}")
            print(f"Size: {img.size}")
            
            exif_data = img.getexif()
            if exif_data:
                relevant_tags = ['Model', 'DateTime']
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in relevant_tags:
                        if isinstance(value, bytes):
                            value = value.decode(errors='replace')
                        print(f"{tag}: {value}")
            
            exif_dict = piexif.load(img.info.get("exif", b""))

            if "GPS" in exif_dict:
                gps_info = exif_dict["GPS"]
                
                lat = gps_info.get(piexif.GPSIFD.GPSLatitude)
                lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef)
                lon = gps_info.get(piexif.GPSIFD.GPSLongitude)
                lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef)
                
                if lat and lon and lat_ref and lon_ref:
                    lat = convert_to_degrees(lat)
                    lon = convert_to_degrees(lon)
                    
                    if lat_ref == b"S":
                        lat = -lat
                    if lon_ref == b"W":
                        lon = -lon
                    
                    return lat, lon
                else:
                    print("No GPS data found in the EXIF information.")
                    return None
            else:
                print("No GPS data found in the EXIF information.")
                return None
    except UnidentifiedImageError:
        print(f"Error: Unsupported image format")
    except IOError as e:
        print(f"Error opening the image file: {e}")
    except Exception as e:
        print(f"Error processing the image EXIF data: {e}")
    return None

def extract_gps_info_video(file_path):
    print_file_info(file_path)
    
    try:
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(file_path)[0]
            
            print(f"Format: {metadata.get('File:FileType', 'Unknown')}")
            print(f"Size: ({metadata.get('File:ImageWidth', 'Unknown')}, {metadata.get('File:ImageHeight', 'Unknown')})")
            
            print(f"Model: {metadata.get('QuickTime:Model', 'Unknown')}")
            create_date = metadata.get('QuickTime:CreateDate', 'Unknown')
            if create_date != 'Unknown':
                create_date = datetime.strptime(create_date, "%Y:%m:%d %H:%M:%S").strftime("%Y:%m:%d %H:%M:%S")
            print(f"DateTime: {create_date}")
            
            lat = metadata.get('Composite:GPSLatitude')
            lon = metadata.get('Composite:GPSLongitude')
            
            if lat is not None and lon is not None:
                return float(lat), float(lon)
            else:
                print("No GPS data found in the video metadata.")
                return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def convert_to_degrees(value):
    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    return d + (m / 60.0) + (s / 3600.0)

def get_location_from_coordinates(lat, lon):
    base_url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "Media GPS Extractor/1.0"
    }
    
    response = requests.get(base_url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        address = data.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village') or 'Unknown'
        return city
    else:
        print(f"Error: Unable to fetch location data. Status code: {response.status_code}")
        return 'Unknown'

def move_to_folder(file_path, folder_name):
    base_dir = os.path.dirname(file_path)
    target_folder = os.path.join(base_dir, folder_name)
    
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    new_file_path = os.path.join(target_folder, os.path.basename(file_path))
    shutil.move(file_path, new_file_path)
    print(f"Moved to: {folder_name}")

def get_creation_time(file_path):
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except (AttributeError, KeyError, IndexError, TypeError, ValueError, IOError):
        pass

    try:
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(file_path)[0]
            create_date = metadata.get('QuickTime:CreateDate') or metadata.get('EXIF:DateTimeOriginal')
            if create_date:
                return datetime.strptime(create_date, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    return datetime.fromtimestamp(os.path.getmtime(file_path))