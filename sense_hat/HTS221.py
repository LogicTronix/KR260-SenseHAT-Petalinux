# Author: Frank Shrestha <frank_shrestha@logictronix.com>

import smbus

# Masks
HTS221_AV_CONF_MASK = 0x3f
HTS221_CTRL1_MASK = 0x87
HTS221_CTRL2_MASK = 0x83
HTS221_CTRL3_MASK = 0xc4
HTS221_STATUS_MASK = 0x3


HTS221_ADDRESS = 0x5f
HTS221_REG_ID = 0x0f
HTS221_ID = 0xbc

# Register map
HTS221_WHO_AM_I = 0x0f
HTS221_AV_CONF = 0x10

HTS221_CTRL1 = 0x20
HTS221_CTRL2 = 0x21
HTS221_CTRL3 = 0x22

HTS221_STATUS = 0x27

HTS221_HUMIDITY_OUT_L = 0x28
HTS221_HUMIDITY_OUT_H = 0x29

HTS221_TEMP_OUT_L = 0x2a
HTS221_TEMP_OUT_H = 0x2b

HTS221_H0_H_2 = 0x30
HTS221_H1_H_2 = 0x31

HTS221_T0_C_8 = 0x32
HTS221_T1_C_8 = 0x33
HTS221_T1_T0 = 0x35

HTS221_H0_T0_OUT = 0x36
HTS221_H1_T0_OUT = 0x3a

HTS221_T0_OUT = 0x3c
HTS221_T1_OUT = 0x3e


def twos_complement(value, bits):
    value = int(value, 2)
    if (value & (1 << (bits - 1))) != 0:
        value = value - (1 << bits)
    return value


def bin_str(number, length):
    return (bin(number)[2:]).zfill(length)


class HTS221():
    def __init__(self, i2c_bus):
        self.bus = smbus.SMBus(i2c_bus)
        self._HTS221_Init()

    def _HTS221_Init(self):
        temp = self.bus.read_byte_data(HTS221_ADDRESS, HTS221_CTRL1)

        temp |= HTS221_CTRL1_MASK

        self.bus.write_byte_data(HTS221_ADDRESS, HTS221_CTRL1, temp)

    def read_temp(self):
        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_T0_C_8 | 0x80, 2)
        tmp = self.bus.read_byte_data(HTS221_ADDRESS, HTS221_T1_T0)

        T0_degC_x8_u16 = ((tmp & 0x03) << 8) | buffer[0]
        T1_degC_x8_u16 = ((tmp & 0x0C) << 6) | buffer[1]

        T0_degC = twos_complement(bin_str((T0_degC_x8_u16 >> 3), 16), 16)
        T1_degC = twos_complement(bin_str((T1_degC_x8_u16 >> 3), 16), 16)

        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_T0_OUT | 0x80, 4)

        T0_out = twos_complement(
            bin_str(((buffer[1] << 8) | buffer[0]), 16), 16)
        T1_out = twos_complement(
            bin_str(((buffer[3] << 8) | buffer[2]), 16), 16)

        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_TEMP_OUT_L | 0x80, 2)

        T_out = twos_complement(
            bin_str(((buffer[1] << 8) | buffer[0]), 16), 16)

        temperature = (T_out - T0_out) * (T1_degC - T0_degC) / \
            (T1_out - T0_out) + T0_degC

        return temperature

    def read_humidity(self):
        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_H0_H_2 | 0x80, 2)

        H0_rh = twos_complement(bin_str((buffer[0] >> 1), 16), 16)
        H1_rh = twos_complement(bin_str((buffer[1] >> 1), 16), 16)

        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_H0_T0_OUT | 0x80, 2)

        H0_T0_out = twos_complement(
            bin_str(((buffer[1] << 8) | buffer[0]), 16), 16)

        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_H1_T0_OUT | 0x80, 2)

        H1_T0_out = twos_complement(
            bin_str(((buffer[1] << 8) | buffer[0]), 16), 16)

        buffer = self.bus.read_i2c_block_data(
            HTS221_ADDRESS, HTS221_HUMIDITY_OUT_L | 0x80, 2)

        H_T_out = twos_complement(
            bin_str(((buffer[1] << 8) | buffer[0]), 16), 16)

        hum = ((H_T_out - H0_T0_out) *
               ((H1_rh - H0_rh) / (H1_T0_out - H0_T0_out))) + H0_rh
        hum *= 10.0

        hum = 1000.0 if (hum > 1000.0) else (0.0 if (hum < 0.0) else hum)

        return hum / 10.0
