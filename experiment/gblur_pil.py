from PIL import Image
from PIL import ImageFilter
import sys


class GaussianBlur(ImageFilter.Filter):
    name = "GaussianBlur"

    def __init__(self, radius=2):
        self.radius = radius

    def filter(self, image):
        return image.gaussian_blur(self.radius)

src_img = Image.open('test.jpg')
src_img.thumbnail((100, 999), Image.ANTIALIAS)
src_img = src_img.filter(GaussianBlur(radius=float(sys.argv[1])))
src_img = src_img.resize((600, 999), Image.ANTIALIAS)

src_img.save('gblur_pil_output.jpg', format="JPEG")
