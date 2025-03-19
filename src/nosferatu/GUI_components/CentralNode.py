from PyQt6.QtCore import Qt, pyqtSignal,pyqtSlot, QThread, QObject
from PyQt6.QtGui import QImage, QPixmap
import sys
import pickle

from ImageHandler import ImageHandler
import FunctionHandler
import ModelHandler
from PIL import Image
from PIL.TiffTags import TAGS_V2
import numpy as np


class CentralNode(QObject):
    """
    The CentralNode is responsible for facilitating communication between the main window and QThread-based worker classes.

    This class sends information to the worker threads, and receives updates from them to forward back to the main window.
    It serves as an intermediary between the GUI and the backend processing threads.

    Attributes:
    """
    update_image = pyqtSignal(QImage)
    def __init__(self, main_window):
        super(CentralNode, self).__init__()
        self.main_window = main_window
        self.current_control=0
        self.image_path=self.metadata=self.image_data=None
        self.image_handler = self.original_image=None
        # Instantiate workers:
        # self.image_handler = ImageHandler() # Add input
        # self.function_handler=FunctionHandler(data="some data")
        # self.model_handler = ModelHandler(data="some data")

        # Connections to MainWindow
        # self.function_handler.update_image.connect()
        # self.image_handler.update_image.connect(self.main_window.displayImage)
        # self.function_handler.update_data.connect()
        # self.build_model.progress_changed.connect(self.main_window.update_progress)
        # self.build_model.status_updated.connect(self.main_window.update_status)
        # self.function_handler.update_model.connect()

    def update_controls(self, current_controls):
        # updates current set of controls based on page number
        self.current_control=current_controls

    def load_image(self,image_path):
        # Open the image using Pillow
        self.image_data = Image.open(image_path)
        self.image_data = self.image_data.convert("RGBA")
        self.original_image=self.image_data
        qimg = self.pil_to_qimage(self.image_data)
        print("emitting image")
        self.update_image.emit(qimg)
        
        # Extract metadata (tags) from the image
        if self.image_data.format == 'TIFF':
            self.metadata = self.image_data.tag_v2
            print("Metadata tags:")
            for tag, value in self.metadata.items():
                tag_name = TAGS_V2.get(tag, tag)
                print(f"{tag_name}: {value}")

    def pil_to_qimage(self, pil_image):
        """Convert a PIL Image to a QImage."""
        qim = None  # Ensure qim is always defined
        if isinstance(pil_image, np.ndarray):
            # Convert the image to raw bytes
            data = pil_image.tobytes("raw")
            # Create a QImage with correct format
            qim = QImage(data, pil_image.shape[1], pil_image.shape[0], pil_image.shape[1] * 4, QImage.Format.Format_RGBA8888)
        elif isinstance(pil_image, Image.Image):
            # Convert from PIL Image to raw bytes (if it’s a PIL Image, not ndarray)
            pil_image = pil_image.convert("RGBA")  # Ensure it’s in RGBA format
            data = pil_image.tobytes("raw")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)

        # Ensure that we always return a valid QImage or None
        return qim
    
    def revert_back_to_original_image(self):
        self.single_image=self.original_image
        return self.single_image


    def apply_filter(self, filter_type):
        image=self.revert_back_to_original_image()
        if isinstance(image, Image.Image):
            image_data = np.array(image)
        self.image_handler = ImageHandler(image)
        self.image_handler.update_image.connect(self.emit_image)
        self.start_processing(self.image_handler)
        self.image_handler.apply_filter_to_image(image_data, filter_type)
        self.image_handler.wait()
        self.single_image=self.image_handler.image_data
        qimg = self.pil_to_qimage(self.single_image)
        # self.update_image.emit(qimg)
        # Connect the image handler's signal to the main window's display method

    def save_single_image(self, file_path):
        """Save the image to the given file path."""
        if self.image_data is not None:
            # Ensure the file path has a valid extension (e.g., .png)
            if not any(file_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']):
                file_path += '.png'  # Default to PNG if no valid extension is found

            if isinstance(self.image_data, Image.Image):
                try:
                    self.image_data.save(file_path)
                    print(f"Image saved to {file_path}")
                except ValueError as e:
                    print(f"Error saving image: {e}")
            elif isinstance(self.image_data, QImage):
                self.image_data.save(file_path)
                print(f"Image saved to {file_path}")
            else:
                print("No valid image data to save.")
        else:
            print("No image data available to save.")


    def emit_image(self, qimage):
        # Emit the updated image to MainWindow
        self.update_image.emit(qimage)
        print('signal emited by CentralNode')
        
    def update_status(self, new_status):
        self.update_status_signal.emit(new_status)

    def start_processing(self, process, **param):
        """
        Start a process.
        """
        process.start()

    def stop_process(self, process):
        """
        Stop a process.
        """
        process.requestInterruption()
        process.wait()