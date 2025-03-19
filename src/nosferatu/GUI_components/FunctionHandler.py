
from PyQt6.QtCore import pyqtSignal, QThread
import pandas as pd

class FunctionHandler(QThread):
    """ Description"""
    update_data = pyqtSignal(pd.DataFrame)
    def __init__(self, FunctionHandler):
        """ doc string"""
        super().__init__()
        self.data=data

    def run(self):
        print("executing function")

                    
