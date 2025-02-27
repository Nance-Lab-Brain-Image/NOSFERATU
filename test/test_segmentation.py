# import module or package here
import unittest
import random
import os

class TestSegmentation(unittest.TestCase):

    def test_bdreg(self):
        test = 0  # remove this line and replace with testing code

    def test_split_images_generates_4_images(self):
        files_to_split_list = ['test_data/image1.png']  # check image type
        split_image_list = split_images(files_to_split_list)
        expected_image_output_list = ['image1_quada.npy',
                                      'image1_quadb.npy',
                                      'image1_quadc.npy',
                                      'image1_quadd.npy']
        for image in expected_image_output_list:
            image = 'test_data/' + image
            self.assertEqual((image, image.is_file()), (image, True))

    def test_split_images_bad_images_quits(self):
        files_to_split_list = ['test_data/image1.badformat']
        with self.assertRaises(TypeError):
            split_image_list = split_images(files_to_split_list)

    def test_split_images_image_does_not_exist(self):
        files_to_split_list = ['test_data/IDONTEXIST.png']
        with self.assertRaises(FileNotFoundError):
            split_image_list = split_images(files_to_split_list)

    def test_split_images_image_already_split(self):
        files_to_split_list = ['test_data/image1.png']
        with self.assertWarns():
            split_image_list_0 = split_images(files_to_split_list)

    def test_image_segmentation(self):
        test = 0

    def test_segmentation_labelling(self):
        test = 0


if __name__ == '__main__':
    unittest.main()
