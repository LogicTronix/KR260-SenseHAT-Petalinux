# KR260-SenseHAT-Petalinux

Integration of RaspberryPi SenseHAT on Kria KR260 with Petalinux

This is a very basic implementation for use with Petalinux.  
This does not currently focus on adding more functionality.  
The primary goal is to add support for Sense HAT.

The `LSM9DS1.py` script is originally written by Tony DiCola  
for Adafruit Industries. The modifications in it is done for making  
it work under Petalinux and removes support for SPI.

# Examples

## Reading Temperature and Humidity from the HTS221 Sensor

```py
from time import sleep

from HTS221 import HTS221

sensor = HTS221(7)

while True:
    print(f'\nTemperature\t: {sensor.read_temp():.4f}° C')
    print(f'Relative Humidity\t: {sensor.read_humidity():.4f} %')
    sleep(1)
```

## Reading Temperature and Pressure from the LPS25H Sensor

```py
from time import sleep

from LPS25H import LPS25H

sensor = LPS25H(7)

while True:
    print(f'\nTemperature\t: {sensor.read_temp():.4f}° C')
    print(f'Pressure\t: {sensor.read_pressure():.4f} hPa')
    sleep(1)
```

## Reading Acceleration, Magnetometer and Gyroscope from the LSM9DS1 Sensor

```py
from time import sleep

from LSM9DS1 import LSM9DS1_I2C

sensor = LSM9DS1_I2C(7)

while True:
    # Read acceleration, magnetometer, gyroscope, temperature.

    accel_x, accel_y, accel_z = sensor.acceleration
    mag_x, mag_y, mag_z = sensor.magnetic
    gyro_x, gyro_y, gyro_z = sensor.gyro
    temp = sensor.temperature

    print("Acceleration (m/s^2): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        accel_x, accel_y, accel_z
    ))

    print("Magnetometer (gauss): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        mag_x, mag_y, mag_z
    ))

    print("Gyroscope (rad/sec): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
        gyro_x, gyro_y, gyro_z
    ))

    print("Temperature: {0:0.3f}° C".format(temp))

    sleep(1)

```
