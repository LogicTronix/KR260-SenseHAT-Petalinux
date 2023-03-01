
import threading
from random import randint

from sense_hat import SenseHat

sense = SenseHat(7)

NUM = 0
COLOUR = [255, 255, 255]


def get_input(sense):
    global NUM, COLOUR

    count = 0

    while True:
        event = sense.stick.wait_for_event()

        if (event.action in ['pressed', 'held']):
            if (event.direction == 'up'):
                count += 1
            elif (event.direction == 'down'):
                count -= 1

        COLOUR = [randint(10, 254), randint(10, 254), randint(10, 254)]
        NUM = count % 10


thread = threading.Thread(target=get_input, args=(sense,))
thread.start()

while True:
    sense.show_letter(str(NUM), text_colour=COLOUR)
