from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap

from skimage import io
from skimage.filters import threshold_li, threshold_mean
from skimage import morphology
from scipy import ndimage
from skimage.measure import label
import numpy as np
from PIL import Image
from PyQt6.QtGui import QImage, QPixmap

class ImageHandler(QThread):
    """
    The ImageHandler class handles image manipulation tasks in a separate thread. 
    It receives image data and processing instructions from the CentralNode, 
    performs the specified transformations or filters on the image, 
    and sends the processed result back to the main window to be displayed.

    Signals:
        update_image (QImage): Emitted to send the processed image back to the main window for display.
    
    Attributes:
        image_data (QImage or np.ndarray): The image data to be processed.
        modify_type (str): The type of modification (e.g., "rotate", "filter", etc.).
    """
    update_image = pyqtSignal(QImage)

    def __init__(self, image_data, **params):
        """
        Initializes the ImageHandler instance with the provided image data and optional parameters.
        
        Args:
            image_data (QImage or np.ndarray): The image data to be processed.
            **params: Additional parameters for processing (e.g., modify_type).
        """
        super().__init__()
        self.image_data = image_data

    def run(self):
        """
        Runs the image manipulation process in a separate thread.
        This method is called automatically when the QThread starts.

        Based on the `modify_type`, it performs different image transformations.
        For now, it just prints "running", but it should include the image processing logic.
        """
        print('Running image processing task...')
        # Here we would add logic for handling different modify_types
        # For example, rotation, filtering, etc.

    def select_function(self):
        """
        Selects the function to be applied based on the current index.

        This is a placeholder function and should be updated to handle different operations.
        """
        if self.current_index == 2:
            self.method = 'PCA'
        else:
            print('Invalid function')

    def apply_filter_to_image(self, image_data, filter_type, channel=0):
        """
        Applies a filter to the input image. The function performs several operations:
        - Converts the image to a single channel.
        - Applies the specified filter.
        - Removes small objects using morphological operations.
        - Fills holes in the binary mask.
        
        Args:
            image_data (np.ndarray): The input image data to be processed.
            filter_type (str): The type of filter to apply ('threshold_li', 'sobel', etc.).
            channel (int): The image channel to use (default is 0, i.e., the first channel).
        
        Returns:
            None: The processed image is emitted via the `update_image` signal.
        """
        print(f'Filter type: {filter_type}')
        if image_data is not None:
            if isinstance(image_data, np.ndarray):
                image = image_data
            else:
                # Convert PIL Image to NumPy array
                image = np.array(image_data)
            print(np.shape(image))

            # Select the specified channel (e.g., Red, Green, Blue)
            image = image_data[:, :, channel]  # Default to channel 0 (Red)

            if filter_type is not None:
                # Apply the selected filter type
                if filter_type == 'threshold_li':
                    threshold = threshold_li(image)  # Apply Li's threshold method
                elif filter_type == 'threshold_mean':
                    threshold = threshold_mean(image)  # Apply Mean threshold method
                else:
                    print('Unknown filter type')
                    return

                # Create binary image after thresholding
                binary_img = image > threshold 

                # Remove small objects from the binary image
                new_img = morphology.remove_small_objects(binary_img, min_size=71)

                # Fill holes in the binary mask
                new_img = ndimage.binary_fill_holes(new_img)
            else:
                # If no filter type is provided, create a blank image
                if isinstance(image_data, np.ndarray):
                    height, width = image_data.shape[:2]  # Get the image dimensions
                else:
                    width, height = image_data.size  # For PIL Image
                new_img = Image.new("L", (width, height), 0)

            # Emit the processed image
            self.emit_updated_image(new_img)
        else:
            print('No image data to process.')

    def emit_updated_image(self, image_data):
        """
        Emits the processed image to the connected slot (e.g., to the main window).

        Args:
            image_data (np.ndarray or Image.Image): The processed image data to be emitted.
        """
        if isinstance(image_data, np.ndarray):  # If the image is in NumPy array format
            # Convert the NumPy array to a PIL Image
            pil_image = Image.fromarray(image_data)
        elif isinstance(image_data, Image.Image):  # If it's already a PIL Image
            pil_image = image_data
        else:
            raise ValueError("Unsupported image data format")

        # If the image is grayscale ('L' mode), convert it to RGBA by adding an alpha channel
        if pil_image.mode == 'L':  # Grayscale image
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)
        else:
            # For RGB or RGBA images, use the "RGBA" mode directly
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)

        # Emit the signal to notify the main window with the updated image
        self.update_image.emit(qim)
        print('Signal emitted by ImageHandler')
