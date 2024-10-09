import piexif
from PIL import Image, ExifTags, UnidentifiedImageError
import pillow_heif
import requests
import os
import shutil
import glob

def print_file_info(path):
    file_name = os.path.basename(path)
    file_size = os.path.getsize(path)
    print(f"File: {file_name}")
    print(f"Size: {file_size} bytes")

def extract_gps_info(file_path):
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

def process_media(file_path):
    coordinates = extract_gps_info(file_path)

    if coordinates:
        lat, lon = coordinates
        print(f"GPS Coordinates: {lat}, {lon}")
        
        city = get_location_from_coordinates(lat, lon)
        print(f"City: {city}")
        
        move_to_folder(file_path, city)
    else:
        print("No location information found.")
        move_to_folder(file_path, 'Unknown')
    print()

SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic']

if __name__ == "__main__":
    folder_path = r"XXXXX"
    unsupported_formats = set()
    files_processed = 0

    for file_path in glob.glob(os.path.join(folder_path, "*.*")):
        files_processed += 1
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in SUPPORTED_IMAGE_FORMATS:
            process_media(file_path)
        else:
            print(f"Unsupported file: {os.path.basename(file_path)}")
            move_to_folder(file_path, 'Not_Supported')
            unsupported_formats.add(file_extension)
            print()

    if files_processed == 0:
        print("No files found to sort.")
    else:
        print(f"Total files processed: {files_processed}")

    if unsupported_formats:
        print("\nUnsupported file formats encountered:")
        for format in unsupported_formats:
            print(f"- {format}")
