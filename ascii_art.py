from PIL import Image
import numpy as np
import requests
import shutil
import os
import argparse
from urllib.parse import urlparse


class AsciiConverter:
    # See http://paulbourke.net/dataformats/asciiart/ for examples of greyscale
    GSCALE1 = '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`\'. '
    GSCALE2 = "@%#*+=-:. "

    def __init__(self, seventy_shades_of_grey, num_columns):
        self.num_columns = num_columns
        self.scale = 0.43  # Good default ratio of w/h for Courier font
        self.seventy_shades_of_grey = seventy_shades_of_grey

    def convert_image_to_greyscale(self, filename):
        self.image = Image.open(filename).convert("L")
        self.image_width, self.image_height = self.image.size[0], self.image.size[1]
        self.tile_width = self.image_width/self.num_columns  # Scale to desired output width
        self.tile_height = self.tile_width/self.scale  # Scale due to ratio and scale of the font
        self.rows = int(self.image_height/self.tile_height)  # Number of rows in the final grid

    def get_average_luminosity(self, image):
        image_array = np.array(image)  # 2D Array of brightness
        width, height = image_array.shape
        return np.average(image_array.reshape(width * height))  # Resize to flat array then compute average brightness

    def generate_ascii_content_of_image(self):
        ascii_image = []

        for j in range(self.rows):
            # Start and ending y-coords of image tiles, convert to int to bucketize
            y1 = int(j * self.tile_height)
            y2 = int((j + 1) * self.tile_height)

            # Because tiling only matches with width and height being exact multiples, correct last tile
            if j == self.rows - 1:
                y2 = self.image_height

            ascii_image.append("")
            for i in range(self.num_columns):
                x1 = int(i * self.tile_width)
                x2 = int((i + 1) * self.tile_width)
                # correct the last tile
                if i == self.num_columns - 1:
                    x2 = self.image_width

                # crop the image to extract the tile into another Image object
                img = self.image.crop((x1, y1, x2, y2))
                # get the average luminace
                average = int(self.get_average_luminosity(img))
                # look up the ASCII character for the greyscale value
                if self.seventy_shades_of_grey:
                    greyscale_value = self.GSCALE1[int((average * 69) / 255)]
                else:
                    greyscale_value = self.GSCALE2[int((average * 9) / 255)]
                # append the ASCII character to the string
                ascii_image[j] += greyscale_value  # TODO GREG slow - update using index
        return ascii_image

    def write_to_text_file(self, ascii_image, output_filename):
        with open(output_filename, 'w') as f:
            for row in ascii_image:
                f.write(row + '\n')


def do_convert(input_filename, output_filename, width=80, seventy_shades_of_grey=False):
    converter = AsciiConverter(seventy_shades_of_grey, width)
    converter.convert_image_to_greyscale(input_filename)
    ascii_image = converter.generate_ascii_content_of_image()
    converter.write_to_text_file(ascii_image, output_filename)


def get_image(url):
    filename = 'input/' + urlparse(url).path.split("/")[-1]
    if not os.path.isfile(filename):
        print("Downloading {} as {}".format(url, filename))
        response = requests.get(url, stream=True)
        with open(filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
    return filename


def download_images(extra_urls):
    urls = [
        # good:
        'https://i.redd.it/707zkx33v1gx.jpg',
        'https://pixabay.com/static/uploads/photo/2013/08/11/19/37/flower-171644_960_720.jpg',
        'https://www.nostarch.com/sites/default/files/imagecache/product_full/pythonplay_cover-front_new.png',
        'http://wiki.gamedetectives.net/images/b/bf/Overwatch_logo.jpg',
        # bad:
        'https://i.redd.it/tm0ulqcxn2gx.jpg',
        'https://i.redd.it/t6favcxj9agx.jpg',
        'https://i.redd.it/7x5l6pdhtagx.jpg',
        'http://i.imgur.com/qN962rH.jpg',
        'http://i.kinja-img.com/gawker-media/image/upload/s---zKMfGT0--/c_scale,fl_progressive,q_80,w_800/19fk32sw3nt1wjpg.jpg'
    ]

    for url in urls + extra_urls:
        try:
            get_image(url)
        except:
            print(
                "Unable to download image {}. "
                "This is a convenience message because it's likely "
                "the hardcoded image selection will disappear.".format(url))


def convert_all_inputdir_files(width):
    for _, _, files in os.walk('input/'):
        for filename in files:
            print("Converting: ", filename)
            input_filename = 'input/' + filename
            output_filename = "output/" + filename.split(".")[0].replace(" ", "_")
            do_convert(input_filename, output_filename + "_10.txt", width, False)
            do_convert(input_filename, output_filename + "_70.txt", width, True)


def main(args):
    download_images(args.urls)
    convert_all_inputdir_files(args.width)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create AsciiArt from images.')
    parser.add_argument('urls', default=[], type=str, nargs='*', help='Urls of images to use.')
    parser.add_argument('--width', nargs="?", metavar='w', default=80, type=int, help='An integer width for the output image.')
    args = parser.parse_args()
    main(args)
