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
    Takes in parameters from CentralNode, modifies them, and sends them to the main window for display.

    This class performs image manipulation tasks in a separate thread. It receives parameters from the CentralNode, 
    processes images, and sends the results back to the main window to be displayed.

    Signals:
        update_image (QImage): Emitted to send the processed image back to the main window for display.
    
    Attributes:
        image_data (QImage): The image data to be processed.
        modify_type (str): The type of modification (e.g., "rotate", "filter", etc.).
    """
    update_image=pyqtSignal(QImage)

    def __init__(self, image_data, **params):
        super().__init__()
        self.image_data = image_data

    def run(self):
        """
        Runs the image manipulation process in a separate thread.
        Based on the `modify_type`, it performs different image transformations.
        """
        print('running')

    def select_function(self):        
        if self.current_index==2:
            self.method=='PCA'
        else:
            print('Invalid function')

    def apply_filter_to_image(self, image_data, filter_type, channel=0):
        """
        Apply a filter to the input image:
        - Convert the image to 1 channel.
        - Apply filter.
        - Remove small objects using morphology.
        - Fill holes in the binary mask.

        Args:
            image_data (np.ndarray): The input image data.
            filter_type (str): The filter type ('threshold_li', 'sobel', etc.)
            channel (int): The channel of the image to use (default is 0).

        Returns:
            None: The filtered image is emitted through the signal.
        """
        print(f'filter_type: {filter_type}')
        if image_data is not None:

            if isinstance(image_data, np.ndarray):
                image = image_data
            else:
                # Convert the PIL Image to NumPy array
                image = np.array(image_data)
            print(np.shape(image))
            image = image_data[:, :, channel]  # Selecting the specified channel (default 0)
            if filter_type is not None:
                # Apply selected filter type
                if filter_type == 'threshold_li':
                    # Li's method thresholding
                    threshold = threshold_li(image)
                if filter_type == 'threshold_mean':
                    threshold = threshold_mean(image)
                else:
                    print('Unknown filter type')
                    pass
                binary_img = image > threshold 
                    # Remove small objects
                new_img = morphology.remove_small_objects(binary_img, min_size=71)
                    # Fill holes in the binary mask
                new_img = ndimage.binary_fill_holes(new_img)
            else:
                if isinstance(image_data, np.ndarray):
                    height, width = image_data.shape[:2]  # Extract height and width
                else:
                    # Otherwise, assume it's a PIL Image
                    width, height = image_data.size
                new_img = Image.new("L", (width, height), 0)
                if isinstance(new_img, np.ndarray):
                    new_img = Image.fromarray((new_img * 255).astype(np.uint8))  # Convert to grayscale PIL image

            # Emit the processed image
            self.emit_updated_image(new_img)
        else:
                pass

    def emit_updated_image(self, image_data):
        """Emit the processed image data to the connected slot."""
        
        if isinstance(image_data, np.ndarray):  # If it's a NumPy array (grayscale or RGB)
            # Convert the NumPy array to a PIL Image
            pil_image = Image.fromarray(image_data)
        elif isinstance(image_data, Image.Image):  # If it's already a PIL Image
            pil_image = image_data
        else:
            raise ValueError("Unsupported image data format")

        # Check if the image is in grayscale (mode "L")
        if pil_image.mode == 'L':  # Grayscale image
            # Convert grayscale image to RGBA by adding an alpha channel
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)
        else:
            # For RGB or RGBA images, you can directly use the "RGBA" mode
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format.Format_RGBA8888)

        # Emit the signal
        self.update_image.emit(qim)
        print('Signal emitted by ImageHandler')
