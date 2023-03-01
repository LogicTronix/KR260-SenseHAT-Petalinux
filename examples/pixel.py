
import threading
from random import randint

from sense_hat import SenseHat

sense = SenseHat(7)

X, Y = 0, 7
COLOUR = [255, 255, 255]


def get_input(sense):
    global X, Y, COLOUR

    while True:
        event = sense.stick.wait_for_event()

        if (event.action in ['pressed', 'held']):
            if (event.direction == 'up'):
                Y = (Y - 1) % 8
            elif (event.direction == 'down'):
                Y = (Y + 1) % 8
            elif (event.direction == 'left'):
                X = (X - 1) % 8
            elif (event.direction == 'right'):
                X = (X + 1) % 8
            else:
                X, Y = 0, 7

        COLOUR = [randint(10, 254), randint(10, 254), randint(10, 254)]


thread = threading.Thread(target=get_input, args=(sense,))
thread.start()

while True:
    sense.set_pixel(X, Y, COLOUR)
