import piexif
from PIL import Image, ExifTags
import pillow_heif
import requests
import time
import os
import shutil
import glob

def print_file_info(path):
    print(f"File path: {path}")
    print(f"File exists: {os.path.exists(path)}")
    print(f"Is file: {os.path.isfile(path)}")
    print(f"File size: {os.path.getsize(path) if os.path.exists(path) else 'N/A'} bytes")

def extract_gps_info(file_path):
    pillow_heif.register_heif_opener()
    
    print_file_info(file_path)
    
    try:
        with Image.open(file_path) as img:
            print(f"Image format: {img.format}")
            print(f"Image size: {img.size}")
            print(f"Image mode: {img.mode}")
            
            exif_data = img.getexif()
            if exif_data:
                print("EXIF Data:")
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        value = value.decode(errors='replace')
                    print(f"{tag}: {value}")
            else:
                print("No EXIF data found in the image.")
            
            exif_dict = piexif.load(img.info["exif"])

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
        "User-Agent": "Image GPS Extractor/1.0"
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

def move_to_city_folder(file_path, city):
    base_dir = os.path.dirname(file_path)
    city_folder = os.path.join(base_dir, city)
    
    if not os.path.exists(city_folder):
        os.makedirs(city_folder)
    
    new_file_path = os.path.join(city_folder, os.path.basename(file_path))
    shutil.move(file_path, new_file_path)
    print(f"Moved {file_path} to {new_file_path}")

def process_image(file_path):
    coordinates = extract_gps_info(file_path)

    if coordinates:
        lat, lon = coordinates
        print(f"\nCalculated GPS Coordinates: {lat}, {lon}")
        
        time.sleep(1)
        
        city = get_location_from_coordinates(lat, lon)
        print(f"City: {city}")
        
        move_to_city_folder(file_path, city)
    else:
        print("GPS information not found in the image.")
        move_to_city_folder(file_path, 'Unknown')

if __name__ == "__main__":
    folder_path = r"XXXXX"
    for file_path in glob.glob(os.path.join(folder_path, "*.HEIC")) + \
                     glob.glob(os.path.join(folder_path, "*.jpg")) + \
                     glob.glob(os.path.join(folder_path, "*.jpeg")):
        process_image(file_path)
