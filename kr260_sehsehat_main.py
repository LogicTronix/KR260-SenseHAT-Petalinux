# examples given in the readme file can be copied and run here

from time import sleep
from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    sense.show_message('Hello World.')

    sense.show_message(f'{sense.get_temperature_from_humidity():.4f}° C')

    sleep(1)
