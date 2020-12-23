# coding: utf-8
import os
import random
from PIL import Image
from PIL import ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype

from io import BytesIO

try:
    from wheezy.captcha import image as wheezy_captcha
except ImportError:
    wheezy_captcha = None

# Note: This file is from an open-source project under the name of "captcha" maintained by
# lepture. This is a copy and modified version of a project's file. Following text is a copy
# of the license included with the project.

"""Copyright (c) 2014, Hsiaoming Yang

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the 
 following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following 
 disclaimer. 

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following 
 disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of the creator nor the names of its contributors may be used to endorse or promote products derived 
 from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
 INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
 SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
 WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
 USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "./data")
DEFAULT_FONTS = [file for file in os.listdir(DATA_DIR)]


__all__ = ["available_options", "ImageCaptcha"]
if wheezy_captcha:
    __all__.append("WheezyCaptcha")
available_options = __all__


table = []
for i in range(256):
    table.append(i * 1.97)


class WheezyCaptcha:
    """Create an image CAPTCHA with wheezy.captcha."""

    def __init__(self, width=200, height=75, fonts=None):
        self.width = width
        self.height = height
        self.fonts = fonts or DEFAULT_FONTS

    # noinspection PyUnresolvedReferences
    def generate(self, chars, file_format="png"):
        """
        Generate an Image Captcha using wheezy method of the given characters.
        """
        if not wheezy_captcha:
            raise AttributeError("wheezy.captcha is not installed.")
        text_drawings = [
            wheezy_captcha.warp(),
            wheezy_captcha.rotate(),
            wheezy_captcha.offset(),
        ]
        capt = wheezy_captcha.captcha(
            drawings=[
                wheezy_captcha.background(),
                wheezy_captcha.text(fonts=self.fonts, drawings=text_drawings),
                wheezy_captcha.curve(),
                wheezy_captcha.noise(),
                wheezy_captcha.smooth(),
            ],
            width=self.width,
            height=self.height,
        )
        im = capt(chars)
        out = BytesIO()
        im.save(out, format=file_format)
        out.seek(0)
        return out


class ImageCaptcha:
    """Create an image CAPTCHA.
    Many of the codes are borrowed from wheezy.captcha, with a modification
    for memory and developer friendly.
    ImageCaptcha has one built-in font, DroidSansMono, which is licensed under
    Apache License 2. You should always use your own fonts::
        captcha = ImageCaptcha(fonts=['/path/to/A.ttf', '/path/to/B.ttf'])
    You can put as many fonts as you like. But be aware of your memory, all of
    the fonts are loaded into your memory, so keep them a lot, but not too
    many.
    :param width: The width of the CAPTCHA image.
    :param height: The height of the CAPTCHA image.
    :param fonts: Fonts to be used to generate CAPTCHA images.
    :param font_sizes: Random choose a font size from this parameters.
    """

    def __init__(self, width=160, height=60, fonts=None, font_sizes=None):
        self.width = width
        self.height = height
        self.fonts = fonts or DEFAULT_FONTS
        self.font_sizes = font_sizes or (42, 50, 56)

    @property
    def truefonts(self):
        return tuple([truetype(n, s) for n in self.fonts for s in self.font_sizes])

    @staticmethod
    def create_noise_curve(image, color):
        w, h = image.size
        x1 = random.randint(0, int(w / 5))
        x2 = random.randint(w - int(w / 5), w)
        y1 = random.randint(int(h / 5), h - int(h / 5))
        y2 = random.randint(y1, h - int(h / 5))
        points = [x1, y1, x2, y2]
        end = random.randint(160, 200)
        start = random.randint(0, 20)
        Draw(image).arc(points, start, end, fill=color)
        return image

    @staticmethod
    def create_noise_dots(image, color, width=3, number=30):
        draw = Draw(image)
        w, h = image.size
        while number:
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            draw.line(((x1, y1), (x1 - 1, y1 - 1)), fill=color, width=width)
            number -= 1
        return image

    def create_captcha_image(self, chars, color, background):
        """Create the CAPTCHA image itself.
        :param chars: text to be generated.
        :param color: color of the text.
        :param background: color of the background.
        The color should be a tuple of 3 numbers, such as (0, 255, 255).
        """
        image = Image.new("RGB", (self.width, self.height), background)
        draw = Draw(image)

        def _draw_character(char):
            font = random.choice(self.truefonts)
            wid, height = draw.textsize(char, font=font)

            dx = random.randint(0, 4)
            dy = random.randint(0, 6)
            im = Image.new("RGBA", (wid + dx, height + dy))
            Draw(im).text((dx, dy), char, font=font, fill=color)

            # rotate
            im = im.crop(im.getbbox())
            im = im.rotate(random.uniform(-30, 30), Image.BILINEAR, expand=1)

            # warp
            dx = wid * random.uniform(0.1, 0.3)
            dy = height * random.uniform(0.2, 0.3)
            x1 = int(random.uniform(-dx, dx))
            y1 = int(random.uniform(-dy, dy))
            x2 = int(random.uniform(-dx, dx))
            y2 = int(random.uniform(-dy, dy))
            w2 = wid + abs(x1) + abs(x2)
            h2 = height + abs(y1) + abs(y2)
            data = (
                x1,
                y1,
                -x1,
                h2 - y2,
                w2 + x2,
                h2 + y2,
                w2 - x2,
                -y1,
            )
            im = im.resize((w2, h2))
            im = im.transform((wid, height), Image.QUAD, data)
            return im

        images = []
        for c in chars:
            if random.random() > 0.5:
                images.append(_draw_character(" "))
            images.append(_draw_character(c))

        text_width = sum([im.size[0] for im in images])

        width = max(text_width, self.width)
        image = image.resize((width, self.height))

        average = int(text_width / len(chars))
        rand = int(0.25 * average)
        offset = int(average * 0.1)

        for im in images:
            wi, he = im.size
            mask = im.convert("L").point(table)
            image.paste(im, (offset, int((self.height - he) / 2)), mask)
            offset = offset + wi + random.randint(-rand, 0)

        if width > self.width:
            image = image.resize((self.width, self.height))

        return image

    def generate_image(self, chars):
        """Generate the image of the given characters.
        :param chars: text to be generated.
        """
        background = random_color(238, 255)
        color = random_color(10, 200, random.randint(220, 255))
        im = self.create_captcha_image(chars, color, background)
        self.create_noise_dots(im, color)
        self.create_noise_curve(im, color)
        im = im.filter(ImageFilter.SMOOTH)
        return im

    def generate(self, chars, file_format="png"):
        im = self.generate_image(chars)
        out = BytesIO()
        im.save(out, format=file_format)
        out.seek(0)
        return out


def random_color(start, end, opacity=None):
    red = random.randint(start, end)
    green = random.randint(start, end)
    blue = random.randint(start, end)
    if opacity is None:
        return red, green, blue
    return red, green, blue, opacity
