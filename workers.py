from PyQt5.QtCore import QThread, pyqtSignal
from utils import (extract_gps_info_image, extract_gps_info_video, 
                   get_location_from_coordinates, move_to_folder, get_creation_time)
from constants import IMAGE_FORMATS, VIDEO_FORMATS, SUPPORTED_MEDIA_FORMATS
import os
import glob
import shutil

class SortByLocThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        unsupported_formats = set()
        files_processed = 0
        total_files = len([f for f in glob.glob(os.path.join(self.folder_path, "*.*"))])

        for file_path in glob.glob(os.path.join(self.folder_path, "*.*")):
            files_processed += 1
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in SUPPORTED_MEDIA_FORMATS:
                self.process_media(file_path)
            else:
                self.update_output.emit(f"Unsupported file: {file_name}")
                move_to_folder(file_path, 'Not Supported')
                unsupported_formats.add(file_extension)
            
            self.update_progress.emit(int(files_processed / total_files * 100))
            self.update_output.emit(f"Processed: {file_name} ({files_processed}/{total_files})")

        if files_processed == 0:
            self.update_output.emit("No files found to sort")
        else:
            self.update_output.emit(f"Total files processed: {files_processed}")

        if unsupported_formats:
            unsupported_str = "\nUnsupported file formats encountered:\n"
            unsupported_str += "\n".join([f"- {format}" for format in unsupported_formats])
            self.update_output.emit(unsupported_str)

        self.finished.emit()

    def process_media(self, file_path):
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_FORMATS:
            coordinates = extract_gps_info_image(file_path)
        elif file_extension in VIDEO_FORMATS:
            coordinates = extract_gps_info_video(file_path)
        else:
            self.update_output.emit(f"Unsupported file: {file_name}")
            move_to_folder(file_path, 'Not Supported')
            return

        if coordinates:
            lat, lon = coordinates
            self.update_output.emit(f"File: {file_name}")
            self.update_output.emit(f"GPS Coordinates: {lat}, {lon}")
            
            city = get_location_from_coordinates(lat, lon)
            self.update_output.emit(f"City: {city}")
            
            move_to_folder(file_path, city)
            self.update_output.emit(f"Moved {file_name} to {city}")
        else:
            self.update_output.emit(f"No location information found for {file_name}")
            move_to_folder(file_path, 'Unknown')
            self.update_output.emit(f"Moved {file_name} to Unknown")
        self.update_output.emit("")

class FlattenFolderThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        file_counts = {}
        total_files = sum([len(files) for r, d, files in os.walk(self.folder_path)])
        processed_files = 0

        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                src_path = os.path.join(root, file)
                
                if file in file_counts:
                    file_counts[file] += 1
                    base_name, ext = os.path.splitext(file)
                    new_file = f"{base_name} {file_counts[file]}{ext}"
                    dest_path = os.path.join(self.folder_path, new_file)
                else:
                    file_counts[file] = 0
                    dest_path = os.path.join(self.folder_path, file.replace('_', ' '))
                
                shutil.move(src_path, dest_path)
                processed_files += 1
                self.update_progress.emit(int(processed_files / total_files * 100))
                self.update_output.emit(f"Moved: {file} ({processed_files}/{total_files})")

        self.finished.emit()

class SortByTimeThread(QThread):
    update_progress = pyqtSignal(int)
    update_output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        files = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
        total_files = len(files)

        for index, file in enumerate(files, 1):
            file_path = os.path.join(self.folder_path, file)
            try:
                date = get_creation_time(file_path)
                
                year_month = date.strftime("%b, %y")
                new_folder = os.path.join(self.folder_path, year_month)
                if not os.path.exists(new_folder):
                    os.makedirs(new_folder)
                
                new_file_path = os.path.join(new_folder, file)
                shutil.move(file_path, new_file_path)
                
                self.update_output.emit(f"Moved {file} to {year_month} ({index}/{total_files})")
            except Exception as e:
                self.update_output.emit(f"Error processing {file}: {str(e)}")
            
            self.update_progress.emit(int(index / total_files * 100))

        self.finished.emit()