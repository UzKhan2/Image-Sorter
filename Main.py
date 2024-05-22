from PIL import Image, ExifTags

# Image File Path
image_path = "xxxxxx"

# Open image
img = Image.open(image_path)

# Extract EXIF data
exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}

# Print metadata
for tag, value in exif.items():
    print(f"{tag}: {value}")
