import threading
from random import randint
from time import sleep

from sense_hat import SenseHat

sense = SenseHat(7)

FUNCTION = None
UNIT = ''
COLOUR = [255, 255, 255]


def get_input(sense):
    global COLOUR, FUNCTION, UNIT

    while True:
        event = sense.stick.wait_for_event()

        if (event.action in ['pressed', 'held']):
            if (event.direction == 'up'):
                FUNCTION = sense.get_humidity
                UNIT = '%'
            elif (event.direction == 'down'):
                FUNCTION = sense.get_pressure
                UNIT = 'hPa'
            elif (event.direction == 'left'):
                FUNCTION = sense.get_accelerometer
                UNIT = 'm/s^2'
            elif (event.direction == 'right'):
                FUNCTION = sense.get_gyroscope
                UNIT = 'rad/sec'
            else:
                FUNCTION = sense.get_temperature_from_humidity
                UNIT = 'C'

        COLOUR = [randint(10, 254), randint(10, 254), randint(10, 254)]


thread = threading.Thread(target=get_input, args=(sense,))
thread.start()

while True:

    if not FUNCTION:
        sense.show_message('Hello World!', text_colour=COLOUR)
        continue

    data = FUNCTION()

    if (type(data) is map):
        x, y, z = data
        info = f'{x:0.3f}, {y:0.3f}, {z:0.3f} {UNIT}'
    else:
        info = f'{data:.3f} {UNIT}'

    print(info)
    sense.show_message(info, text_colour=COLOUR)

    sleep(0.5)
