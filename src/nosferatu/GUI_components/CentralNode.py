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
    The CentralNode is responsible for facilitating communication between the main window 
    and QThread-based worker classes. It acts as an intermediary between the GUI (main window) 
    and backend processing threads (such as image processing and model building).
    
    Attributes:
    update_image (pyqtSignal): Signal emitted to update the image in the main window.
    main_window (MainWindow): Reference to the main window instance for UI updates.
    current_control (int): Keeps track of the current control index (e.g., page number).
    image_path (str): Path to the currently loaded image.
    metadata (dict): Metadata tags extracted from the loaded image.
    image_data (Image.Image or None): The image data of the loaded image.
    original_image (Image.Image or None): The original image data before processing.
    image_handler (ImageHandler or None): The handler responsible for image manipulation and processing.
    """
    update_image = pyqtSignal(QImage)

    def __init__(self, main_window):
        """
        Initializes the CentralNode instance and sets up connections to worker classes and main window.
        
        Args:
            main_window (MainWindow): The main window instance to update the UI based on backend operations.
        """
        super(CentralNode, self).__init__()
        self.main_window = main_window
        self.current_control = 0
        self.image_path = self.metadata = self.image_data = None
        self.image_handler = self.original_image = None

        # Placeholder for worker instances
        # self.image_handler = ImageHandler()  # Example image handler
        # self.function_handler = FunctionHandler(data="some data")  # Example function handler
        # self.model_handler = ModelHandler(data="some data")  # Example model handler

        # Connections to MainWindow (Example)
        # self.function_handler.update_image.connect(self.main_window.displayImage)
        # self.image_handler.update_image.connect(self.main_window.displayImage)
        # self.function_handler.update_data.connect(self.main_window.update_data)
        # self.build_model.progress_changed.connect(self.main_window.update_progress)
        # self.build_model.status_updated.connect(self.main_window.update_status)
        # self.function_handler.update_model.connect(self.main_window.update_model)

    def update_controls(self, current_controls):
        """
        Updates the current set of controls (e.g., page number) based on the page number.

        Args:
            current_controls (int): The new control index (e.g., page number).
        """
        self.current_control = current_controls

    def load_image(self, image_path):
        """
        Loads an image from the specified path, extracts metadata if available, and emits the image to the main window.

        Args:
            image_path (str): The path to the image file to load.
        """
        # Open the image using Pillow
        self.image_data = Image.open(image_path)
        self.image_data = self.image_data.convert("RGBA")  # Ensure the image is in RGBA format
        self.original_image = self.image_data  # Store original image

        # Convert Pillow image to QImage for display in GUI
        qimg = self.pil_to_qimage(self.image_data)
        print("Emitting image to main window...")
        self.update_image.emit(qimg)  # Emit the image for UI update
        
        # Extract metadata (tags) from TIFF images
        if self.image_data.format == 'TIFF':
            self.metadata = self.image_data.tag_v2
            print("Metadata tags:")
            for tag, value in self.metadata.items():
                tag_name = TAGS_V2.get(tag, tag)
                print(f"{tag_name}: {value}")

    def pil_to_qimage(self, pil_image):
        """
        Converts a PIL Image to a QImage for use in the Qt GUI.

        Args:
            pil_image (PIL.Image.Image or np.ndarray): The PIL image to convert.

        Returns:
            QImage: The converted QImage object.
        """
        qim = None  # Default value for QImage

        if isinstance(pil_image, np.ndarray):
            # Convert numpy ndarray to QImage (raw byte data format)
            data = pil_image.tobytes("raw")
            qim = QImage(data, pil_image.shape[1], pil_image.shape[0], pil_image.shape[1] * 4, QImage.Format.Format_RGBA8888)
        elif isinstance(pil_image, Image.Image):
            # Convert from PIL Image to raw bytes (ensure RGBA format)
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)

        # Return the QImage or None if conversion failed
        return qim
    
    def revert_back_to_original_image(self):
        """
        Reverts any modifications and returns the original loaded image.

        Returns:
            Image.Image: The original image before any processing.
        """
        self.single_image = self.original_image
        return self.single_image

    def apply_filter(self, filter_type):
        """
        Applies a filter to the image based on the given filter type.

        Args:
            filter_type (str): The type of filter to apply (e.g., "blur", "sharpen").
        """
        # Get the original image
        image = self.revert_back_to_original_image()

        if isinstance(image, Image.Image):
            image_data = np.array(image)  # Convert to numpy array for processing

        # Create the image handler and connect the image update signal
        self.image_handler = ImageHandler(image)
        self.image_handler.update_image.connect(self.emit_image)

        # Start the processing in the worker thread
        self.start_processing(self.image_handler)

        # Apply the filter
        self.image_handler.apply_filter_to_image(image_data, filter_type)
        self.image_handler.wait()  # Wait for processing to complete

        # Get the processed image and emit it
        self.single_image = self.image_handler.image_data
        qimg = self.pil_to_qimage(self.single_image)
        # self.update_image.emit(qimg)  # Uncomment if emitting the image after filtering

    def save_single_image(self, file_path):
        """
        Saves the currently loaded image to a specified file path.

        Args:
            file_path (str): The path where the image should be saved.
        """
        if self.image_data is not None:
            # Ensure the file path has a valid image extension (e.g., .png)
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
        """
        Emits the updated image to the main window for display.

        Args:
            qimage (QImage): The updated QImage to be displayed in the main window.
        """
        self.update_image.emit(qimage)
        print('Signal emitted by CentralNode')

    def update_status(self, new_status):
        """
        Updates the status of the operation in the main window.

        Args:
            new_status (str): The new status message to display in the main window.
        """
        self.update_status_signal.emit(new_status)

    def start_processing(self, process, **param):
        """
        Starts a background process (e.g., an image processing task).

        Args:
            process (QThread): The process to be started.
            **param: Additional parameters to be passed to the process.
        """
        process.start()

    def stop_process(self, process):
        """
        Stops a background process if needed.

        Args:
            process (QThread): The process to stop.
        """
        process.requestInterruption()
        process.wait()
