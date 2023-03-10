# KR260-SenseHAT

Integration of RaspberryPi SenseHAT on Kria KR260 with Petalinux

![Block Design](block_design.png)

This is a very basic implementation for use with Petalinux. This does not currently focus on adding more functionality.
The primary goal is to add support for Sense HAT.

The `LSM9DS1.py` script is originally written by Tony DiCola for Adafruit Industries.  
The modifications in it is done for making it work under Petalinux and removes support for SPI.

**Update**:  
This is now a modified form of https://github.com/astro-pi/python-sense-hat  
and offers the same methods and properties. However, not all methods and  
properties are supported.

> Please read the description of the methods you are using.

## Repo Structure

```tree
KR260-SenseHAT
│
├── design_files             // Vivado and Petalinux design files
│   ├── kr260.bin
│   ├── kr260.bit            // Bitstream file
│   ├── kr260.bsp            // Customized Board Support Package
│   ├── kr260.xdc            // Vivado design constraints
│   ├── kr260.xsa            // Xilinx Support Archive
│   ├── kr260_bd.tcl         // Vivado block design TCL file
│   ├── pl.dtsi              // Modified device tree source include file, includes rpi-sense node
│   └── pl_original.dtsi     // Original device tree source include file created using XSCT
│
├── driver                   // Sense HAT driver files from the Raspberry Pi linux repo
│   ├── Makefile
│   ├── core.h
│   ├── framebuffer.h
│   ├── joystick.h
│   ├── rpisense-core.c
│   ├── rpisense-fb.c
│   └── rpisense-js.c
│
├── examples                 // Python example files
│   ├── counter.py           // Simple counter 0-9
│   ├── image.py             // Displays 8x8 RPi logo
│   ├── pixel.py             // Move pixel with joystick
│   └── rpi.png              // 8x8 RPi logo
│
├── sense_hat                // Sense HAT python package
│   ├── HTS221.py
│   ├── LPS25H.py
│   ├── LSM9DS1.py
│   ├── __init__.py
│   ├── colour.py
│   ├── exceptions.py
│   ├── sense_hat.py
│   ├── sense_hat_text.png
│   ├── sense_hat_text.txt
│   └── stick.py
│
├── LICENSE
├── README.md
├── block_design.png         // Vivado block design
└── main.py                  // Example python file, switch sensor reading with joystick
```

## Available Properties

-   humidity
-   temp
-   temperature
-   pressure
-   magnetic
-   compass_raw
-   gyro
-   gyroscope
-   gyro_raw
-   gyroscope_raw
-   accel
-   accelerometer
-   accel_raw
-   accelerometer_raw

## Available Methods

-   show_message()
-   get_humidity()
-   get_temperature_from_humidity()
-   get_temperature_from_pressure()
-   get_temperature()
-   get_pressure()
-   get_compass_raw()
-   get_gyroscope()
-   get_gyroscope_raw()
-   get_accelerometer()
-   get_accelerometer_raw()

# Examples

## Reading Temperature, Humidity and Pressure

```py
from time import sleep
from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    # Temperature
    print(f'\nTemperature\t: {sense.temp:.4f}° C')
    print(f'\nTemperature\t: {sense.temperature:.4f}° C')

    print(f'\nTemperature\t: {sense.get_temperature_from_humidity():.4f}° C')
    print(f'\nTemperature\t: {sense.get_temperature_from_pressure():.4f}° C')
    print(f'\nTemperature\t: {sense.get_temperature():.4f}° C')

    # Humidity
    print(f'Relative Humidity\t: {sense.humidity:.4f} %')
    print(f'Relative Humidity\t: {sense.get_humidity():.4f} %')

    # Pressure
    print(f'Pressure\t: {sensor.pressure():.4f} hPa')
    print(f'Pressure\t: {sensor.get_pressure():.4f} hPa')

    sleep(1)
```

## Reading Acceleration, Magnetometer and Gyroscope

```py
from time import sleep
from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    # Read acceleration, magnetometer, gyroscope

    accel_x, accel_y, accel_z = sense.accelerometer
    mag_x, mag_y, mag_z = sense.magnetic
    gyro_x, gyro_y, gyro_z = sense.gyro

    print("Acceleration (m/s^2): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        accel_x, accel_y, accel_z
    ))

    print("Magnetometer (gauss): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        mag_x, mag_y, mag_z
    ))

    print("Gyroscope (rad/sec): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        gyro_x, gyro_y, gyro_z
    ))

    sleep(1)

```

## Displaying Information on the LED Matrix

```py
from time import sleep
from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    sense.show_message('Hello World.')

    sense.show_message(f'{sense.get_temperature_from_humidity():.4f}° C')

    sleep(1)

```

## Displaying 8x8 RPi Logo on the LED Matrix

```py
from sense_hat import SenseHat

# 7 is I2C bus
sense = SenseHat(7)

while True:
    sense.load_image('rpi.png', redraw=True)

```
