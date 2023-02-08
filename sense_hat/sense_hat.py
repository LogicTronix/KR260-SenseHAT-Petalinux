#!/usr/bin/python
import logging
import struct
import os
import time
import numpy as np
import glob
import array
import fcntl
from PIL import Image  # pillow

from .stick import SenseStick
from .colour import ColourSensor
from .exceptions import ColourSensorInitialisationError

from .HTS221 import HTS221
from .LPS25H import LPS25H
from .LSM9DS1 import LSM9DS1_I2C


class SenseHat(object):

    SENSE_HAT_FB_NAME = 'RPi-Sense FB'
    SENSE_HAT_FB_FBIOGET_GAMMA = 61696
    SENSE_HAT_FB_FBIOSET_GAMMA = 61697
    SENSE_HAT_FB_FBIORESET_GAMMA = 61698
    SENSE_HAT_FB_GAMMA_DEFAULT = 0
    SENSE_HAT_FB_GAMMA_LOW = 1
    SENSE_HAT_FB_GAMMA_USER = 2

    def __init__(
            self,
            i2c_bus,
            text_assets='sense_hat_text'
        ):

        self.bus = i2c_bus

        self._fb_device = self._get_fb_device()
        if self._fb_device is None:
            raise OSError('Cannot detect %s device' % self.SENSE_HAT_FB_NAME)

        if not glob.glob('/dev/i2c*'):
            raise OSError('Cannot access I2C. Please ensure I2C is enabled in raspi-config')

        # 0 is With B+ HDMI port facing downwards
        pix_map0 = np.array([
             [0,  1,  2,  3,  4,  5,  6,  7],
             [8,  9, 10, 11, 12, 13, 14, 15],
            [16, 17, 18, 19, 20, 21, 22, 23],
            [24, 25, 26, 27, 28, 29, 30, 31],
            [32, 33, 34, 35, 36, 37, 38, 39],
            [40, 41, 42, 43, 44, 45, 46, 47],
            [48, 49, 50, 51, 52, 53, 54, 55],
            [56, 57, 58, 59, 60, 61, 62, 63]
        ], int)

        pix_map90 = np.rot90(pix_map0)
        pix_map180 = np.rot90(pix_map90)
        pix_map270 = np.rot90(pix_map180)

        self._pix_map = {
              0: pix_map0,
             90: pix_map90,
            180: pix_map180,
            270: pix_map270
        }

        self._rotation = 0

        # Load text assets
        dir_path = os.path.dirname(__file__)
        self._load_text_assets(
            os.path.join(dir_path, '%s.png' % text_assets),
            os.path.join(dir_path, '%s.txt' % text_assets)
        )

        self._humidity = HTS221(self.bus)
        self._pressure = LPS25H(self.bus)

        self._imu = LSM9DS1_I2C(self.bus)
        self._stick = SenseStick()

        # initialise the TCS34725 colour sensor (if possible)
        try:
            self._colour = ColourSensor()
        except Exception as e:
            logging.debug(e)
            pass

    ####
    # Text assets
    ####

    # Text asset files are rotated right through 90 degrees to allow blocks of
    # 40 contiguous pixels to represent one 5 x 8 character. These are stored
    # in a 8 x 640 pixel png image with characters arranged adjacently
    # Consequently we must rotate the pixel map left through 90 degrees to
    # compensate when drawing text

    def _load_text_assets(self, text_image_file, text_file):
        """
        Internal. Builds a character indexed dictionary of pixels used by the
        show_message function below
        """

        text_pixels = self.load_image(text_image_file, False)
        with open(text_file, 'r') as f:
            loaded_text = f.read()
        self._text_dict = {}
        for index, s in enumerate(loaded_text):
            start = index * 40
            end = start + 40
            char = text_pixels[start:end]
            self._text_dict[s] = char

    def _trim_whitespace(self, char):  # For loading text assets only
        """
        Internal. Trims white space pixels from the front and back of loaded
        text characters
        """

        psum = lambda x: sum(sum(x, []))
        if psum(char) > 0:
            is_empty = True
            while is_empty:  # From front
                row = char[0:8]
                is_empty = psum(row) == 0
                if is_empty:
                    del char[0:8]
            is_empty = True
            while is_empty:  # From back
                row = char[-8:]
                is_empty = psum(row) == 0
                if is_empty:
                    del char[-8:]
        return char

    def _get_fb_device(self):
        """
        Internal. Finds the correct frame buffer device for the sense HAT
        and returns its /dev name.
        """

        device = None

        for fb in glob.glob('/sys/class/graphics/fb*'):
            name_file = os.path.join(fb, 'name')
            if os.path.isfile(name_file):
                with open(name_file, 'r') as f:
                    name = f.read()
                if name.strip() == self.SENSE_HAT_FB_NAME:
                    fb_device = fb.replace(os.path.dirname(fb), '/dev')
                    if os.path.exists(fb_device):
                        device = fb_device
                        break

        return device

    ####
    # Joystick
    ####

    @property
    def stick(self):
        return self._stick

    ####
    # Colour sensor
    ####

    @property
    def colour(self):
        try:
            return self._colour
        except AttributeError as e:
            raise ColourSensorInitialisationError(
                explanation="This Sense HAT" +
                            " does not have a color sensor") from e

    color = colour

    def has_colour_sensor(self):
        try:
            self._colour
        except:
            return False
        else:
            return True

    ####
    # LED Matrix
    ####

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, r):
        self.set_rotation(r, True)

    def set_rotation(self, r=0, redraw=True):
        """
        Sets the LED matrix rotation for viewing, adjust if the Pi is upside
        down or sideways. 0 is with the Pi HDMI port facing downwards
        """

        if r in self._pix_map.keys():
            if redraw:
                pixel_list = self.get_pixels()
            self._rotation = r
            if redraw:
                self.set_pixels(pixel_list)
        else:
            raise ValueError('Rotation must be 0, 90, 180 or 270 degrees')

    def _pack_bin(self, pix):
        """
        Internal. Encodes python list [R,G,B] into 16 bit RGB565
        """

        r = (pix[0] >> 3) & 0x1F
        g = (pix[1] >> 2) & 0x3F
        b = (pix[2] >> 3) & 0x1F
        bits16 = (r << 11) + (g << 5) + b
        return struct.pack('H', bits16)

    def _unpack_bin(self, packed):
        """
        Internal. Decodes 16 bit RGB565 into python list [R,G,B]
        """

        output = struct.unpack('H', packed)
        bits16 = output[0]
        r = (bits16 & 0xF800) >> 11
        g = (bits16 & 0x7E0) >> 5
        b = (bits16 & 0x1F)
        return [int(r << 3), int(g << 2), int(b << 3)]

    def flip_h(self, redraw=True):
        """
        Flip LED matrix horizontal
        """

        pixel_list = self.get_pixels()
        flipped = []
        for i in range(8):
            offset = i * 8
            flipped.extend(reversed(pixel_list[offset:offset + 8]))
        if redraw:
            self.set_pixels(flipped)
        return flipped

    def flip_v(self, redraw=True):
        """
        Flip LED matrix vertical
        """

        pixel_list = self.get_pixels()
        flipped = []
        for i in reversed(range(8)):
            offset = i * 8
            flipped.extend(pixel_list[offset:offset + 8])
        if redraw:
            self.set_pixels(flipped)
        return flipped

    def set_pixels(self, pixel_list):
        """
        Accepts a list containing 64 smaller lists of [R,G,B] pixels and
        updates the LED matrix. R,G,B elements must integers between 0
        and 255
        """

        if len(pixel_list) != 64:
            raise ValueError('Pixel lists must have 64 elements')

        for index, pix in enumerate(pixel_list):
            if len(pix) != 3:
                raise ValueError('Pixel at index %d is invalid. Pixels must contain 3 elements: Red, Green and Blue' % index)

            for element in pix:
                if element > 255 or element < 0:
                    raise ValueError('Pixel at index %d is invalid. Pixel elements must be between 0 and 255' % index)

        with open(self._fb_device, 'wb') as f:
            map = self._pix_map[self._rotation]
            for index, pix in enumerate(pixel_list):
                # Two bytes per pixel in fb memory, 16 bit RGB565
                f.seek(map[index // 8][index % 8] * 2)  # row, column
                f.write(self._pack_bin(pix))

    def get_pixels(self):
        """
        Returns a list containing 64 smaller lists of [R,G,B] pixels
        representing what is currently displayed on the LED matrix
        """

        pixel_list = []
        with open(self._fb_device, 'rb') as f:
            map = self._pix_map[self._rotation]
            for row in range(8):
                for col in range(8):
                    # Two bytes per pixel in fb memory, 16 bit RGB565
                    f.seek(map[row][col] * 2)  # row, column
                    pixel_list.append(self._unpack_bin(f.read(2)))
        return pixel_list

    def set_pixel(self, x, y, *args):
        """
        Updates the single [R,G,B] pixel specified by x and y on the LED matrix
        Top left = 0,0 Bottom right = 7,7

        e.g. ap.set_pixel(x, y, r, g, b)
        or
        pixel = (r, g, b)
        ap.set_pixel(x, y, pixel)
        """

        pixel_error = 'Pixel arguments must be given as (r, g, b) or r, g, b'

        if len(args) == 1:
            pixel = args[0]
            if len(pixel) != 3:
                raise ValueError(pixel_error)
        elif len(args) == 3:
            pixel = args
        else:
            raise ValueError(pixel_error)

        if x > 7 or x < 0:
            raise ValueError('X position must be between 0 and 7')

        if y > 7 or y < 0:
            raise ValueError('Y position must be between 0 and 7')

        for element in pixel:
            if element > 255 or element < 0:
                raise ValueError('Pixel elements must be between 0 and 255')

        with open(self._fb_device, 'wb') as f:
            map = self._pix_map[self._rotation]
            # Two bytes per pixel in fb memory, 16 bit RGB565
            f.seek(map[y][x] * 2)  # row, column
            f.write(self._pack_bin(pixel))

    def get_pixel(self, x, y):
        """
        Returns a list of [R,G,B] representing the pixel specified by x and y
        on the LED matrix. Top left = 0,0 Bottom right = 7,7
        """

        if x > 7 or x < 0:
            raise ValueError('X position must be between 0 and 7')

        if y > 7 or y < 0:
            raise ValueError('Y position must be between 0 and 7')

        pix = None

        with open(self._fb_device, 'rb') as f:
            map = self._pix_map[self._rotation]
            # Two bytes per pixel in fb memory, 16 bit RGB565
            f.seek(map[y][x] * 2)  # row, column
            pix = self._unpack_bin(f.read(2))

        return pix

    def load_image(self, file_path, redraw=True):
        """
        Accepts a path to an 8 x 8 image file and updates the LED matrix with
        the image
        """

        if not os.path.exists(file_path):
            raise IOError('%s not found' % file_path)

        img = Image.open(file_path).convert('RGB')
        pixel_list = list(map(list, img.getdata()))

        if redraw:
            self.set_pixels(pixel_list)

        return pixel_list

    def clear(self, *args):
        """
        Clears the LED matrix with a single colour, default is black / off

        e.g. ap.clear()
        or
        ap.clear(r, g, b)
        or
        colour = (r, g, b)
        ap.clear(colour)
        """

        black = (0, 0, 0)  # default

        if len(args) == 0:
            colour = black
        elif len(args) == 1:
            colour = args[0]
        elif len(args) == 3:
            colour = args
        else:
            raise ValueError('Pixel arguments must be given as (r, g, b) or r, g, b')

        self.set_pixels([colour] * 64)

    def _get_char_pixels(self, s):
        """
        Internal. Safeguards the character indexed dictionary for the
        show_message function below
        """

        if len(s) == 1 and s in self._text_dict.keys():
            return list(self._text_dict[s])
        else:
            return list(self._text_dict['?'])

    def show_message(
            self,
            text_string,
            scroll_speed=.1,
            text_colour=[255, 255, 255],
            back_colour=[0, 0, 0]
        ):
        """
        Scrolls a string of text across the LED matrix using the specified
        speed and colours
        """

        # We must rotate the pixel map left through 90 degrees when drawing
        # text, see _load_text_assets
        previous_rotation = self._rotation
        self._rotation -= 90
        if self._rotation < 0:
            self._rotation = 270
        dummy_colour = [None, None, None]
        string_padding = [dummy_colour] * 64
        letter_padding = [dummy_colour] * 8
        # Build pixels from dictionary
        scroll_pixels = []
        scroll_pixels.extend(string_padding)
        for s in text_string:
            scroll_pixels.extend(self._trim_whitespace(self._get_char_pixels(s)))
            scroll_pixels.extend(letter_padding)
        scroll_pixels.extend(string_padding)
        # Recolour pixels as necessary
        coloured_pixels = [
            text_colour if pixel == [255, 255, 255] else back_colour
            for pixel in scroll_pixels
        ]
        # Shift right by 8 pixels per frame to scroll
        scroll_length = len(coloured_pixels) // 8
        for i in range(scroll_length - 8):
            start = i * 8
            end = start + 64
            self.set_pixels(coloured_pixels[start:end])
            time.sleep(scroll_speed)
        self._rotation = previous_rotation

    def show_letter(
            self,
            s,
            text_colour=[255, 255, 255],
            back_colour=[0, 0, 0]
        ):
        """
        Displays a single text character on the LED matrix using the specified
        colours
        """

        if len(s) > 1:
            raise ValueError('Only one character may be passed into this method')
        # We must rotate the pixel map left through 90 degrees when drawing
        # text, see _load_text_assets
        previous_rotation = self._rotation
        self._rotation -= 90
        if self._rotation < 0:
            self._rotation = 270
        dummy_colour = [None, None, None]
        pixel_list = [dummy_colour] * 8
        pixel_list.extend(self._get_char_pixels(s))
        pixel_list.extend([dummy_colour] * 16)
        coloured_pixels = [
            text_colour if pixel == [255, 255, 255] else back_colour
            for pixel in pixel_list
        ]
        self.set_pixels(coloured_pixels)
        self._rotation = previous_rotation

    @property
    def gamma(self):
        buffer = array.array('B', [0]*32)
        with open(self._fb_device) as f:
            fcntl.ioctl(f, self.SENSE_HAT_FB_FBIOGET_GAMMA, buffer)
        return list(buffer)

    @gamma.setter
    def gamma(self, buffer):
        if len(buffer) != 32:
            raise ValueError('Gamma array must be of length 32')

        if not all(b <= 31 for b in buffer):
            raise ValueError('Gamma values must be bewteen 0 and 31')

        if not isinstance(buffer, array.array):
            buffer = array.array('B', buffer)

        with open(self._fb_device) as f:
            fcntl.ioctl(f, self.SENSE_HAT_FB_FBIOSET_GAMMA, buffer)

    def gamma_reset(self):
        """
        Resets the LED matrix gamma correction to default
        """

        with open(self._fb_device) as f:
            fcntl.ioctl(f, self.SENSE_HAT_FB_FBIORESET_GAMMA, self.SENSE_HAT_FB_GAMMA_DEFAULT)

    @property
    def low_light(self):
        return self.gamma == [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 10, 10]

    @low_light.setter
    def low_light(self, value):
        with open(self._fb_device) as f:
            cmd = self.SENSE_HAT_FB_GAMMA_LOW if value else self.SENSE_HAT_FB_GAMMA_DEFAULT
            fcntl.ioctl(f, self.SENSE_HAT_FB_FBIORESET_GAMMA, cmd)

    ####
    # Environmental sensors
    ####


    def get_humidity(self):
        """
        Returns the percentage of relative humidity
        """
        return self._humidity.read_humidity()

    @property
    def humidity(self):
        return self.get_humidity()

    def get_temperature_from_humidity(self):
        """
        Returns the temperature in Celsius from the humidity sensor
        """

        return self._humidity.read_temp()

    def get_temperature_from_pressure(self):
        """
        Returns the temperature in Celsius from the pressure sensor
        """
        return self._pressure.read_temp()

    def get_temperature(self):
        """
        Returns the temperature in Celsius
        """

        return self.get_temperature_from_humidity()

    @property
    def temp(self):
        return self.get_temperature_from_humidity()

    @property
    def temperature(self):
        return self.get_temperature_from_humidity()

    def get_pressure(self):
        """
        Returns the pressure in Millibars
        """
        return self._pressure.read_pressure()

    @property
    def pressure(self):
        return self.get_pressure()

    ####
    # IMU Sensor
    ####

    @property
    def magnetic(self):
        return self._imu.magnetic

    def get_compass_raw(self):
        """Read the raw magnetometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the magnetometer in nice units you probably want to use the
        magnetometer property!
        """

        return self._imu.read_mag_raw()

    @property
    def compass_raw(self):
        return self.get_compass_raw()

    def get_gyroscope(self):
        """The gyroscope X, Y, Z axis values as a 3-tuple of
        rad/s values.
        """

        return self._imu.gyro

    @property
    def gyro(self):
        return self.get_gyroscope()

    @property
    def gyroscope(self):
        return self.get_gyroscope()

    def get_gyroscope_raw(self):
        """Read the raw gyroscope sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the gyroscope in nice units you probably want to use the
        gyroscope property!
        """
        return self._imu.read_gyro_raw()

    @property
    def gyro_raw(self):
        return self.get_gyroscope_raw()

    @property
    def gyroscope_raw(self):
        return self.get_gyroscope_raw()

    def get_accelerometer(self):
        """The accelerometer X, Y, Z axis values as a 3-tuple of
        :math:`m/s^2` values.
        """

        return self._imu.acceleration

    @property
    def accel(self):
        return self.get_accelerometer()

    @property
    def accelerometer(self):
        return self.get_accelerometer()

    def get_accelerometer_raw(self):
        """Read the raw accelerometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the acceleration in nice units you probably want to use the
        accelerometer property!
        """
        return self._imu.read_accel_raw()

    @property
    def accel_raw(self):
        return self.get_accelerometer_raw()

    @property
    def accelerometer_raw(self):
        return self.get_accelerometer_raw()
