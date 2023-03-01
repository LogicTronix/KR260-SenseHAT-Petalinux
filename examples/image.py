from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    sense.load_image('rpi.png', redraw=True)
