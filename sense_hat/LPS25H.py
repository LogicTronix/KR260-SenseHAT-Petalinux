# Author: Frank Shrestha <frank_shrestha@logictronix.com>

import smbus

LPS25H_ADDRESS = 0x5c

LPS25H_WHO_AM_I = 0x0F         # R
LPS25H_RES_CONF = 0x10         # R/W

# Averaging : 512 for pressure and 64 for temperature
LPS25H_RES_CONF_MASK = 0x0F

LPS25H_REF_P_XL = 0x08          # R/W
LPS25H_REF_P_L = 0x09           # R/W
LPS25H_REF_P_H = 0x0A          # R/W

LPS25H_CTRL_REG1 = 0x20        # R/W
LPS25H_CTRL_REG2 = 0x21        # R/W
LPS25H_CTRL_REG3 = 0x22        # R/W
LPS25H_CTRL_REG4 = 0x23        # R/W

LPS25H_CTRL_REG1_MASK = 0xcc
LPS25H_CTRL_REG2_MASK = 0xc0

LPS25H_INT_CFG = 0x24          # R/W
LPS25H_INT_SOURCE = 0x25       # R

LPS25H_STATUS_REG = 0x27       # R

LPS25H_PRESS_POUT_XL = 0x28    # R
LPS25H_PRESS_OUT_L = 0x29      # R
LPS25H_PRESS_OUT_H = 0x2A      # R

LPS25H_TEMP_OUT_L = 0x2B       # R
LPS25H_TEMP_OUT_H = 0x2C       # R

LPS25H_FIFO_CTRL = 0x2E        # R/W
LPS25H_FIFO_STATUS = 0x2F      # R

LPS25H_FIFO_CTRL_MASK = 0x40

LPS25H_THS_P_L = 0x30          # R/W
LPS25H_THS_P_H = 0x31          # R/W

LPS25H_RPDS_L = 0x39           # R/W
LPS25H_RPDS_H = 0x3A           # R/W


def twos_complement(value, bits):
    value = int(value, 2)
    if (value & (1 << (bits - 1))) != 0:
        value = value - (1 << bits)
    return value


def bin_str(number, length):
    return (bin(number)[2:]).zfill(length)


class LPS25H():
    def __init__(self, i2c_bus):
        self.bus = smbus.SMBus(i2c_bus)
        self._LPS25H_Init()

    def _LPS25H_Init(self):
        temp = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_CTRL_REG1)
        temp |= LPS25H_CTRL_REG1_MASK
        self.bus.write_byte_data(LPS25H_ADDRESS, LPS25H_CTRL_REG1, temp)

        temp = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_RES_CONF)
        temp |= LPS25H_RES_CONF_MASK
        self.bus.write_byte_data(LPS25H_ADDRESS, LPS25H_RES_CONF, temp)

        temp = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_FIFO_CTRL)
        temp |= LPS25H_FIFO_CTRL_MASK
        self.bus.write_byte_data(LPS25H_ADDRESS, LPS25H_FIFO_CTRL, temp)

        temp = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_CTRL_REG2)
        temp |= LPS25H_CTRL_REG2_MASK
        self.bus.write_byte_data(LPS25H_ADDRESS, LPS25H_CTRL_REG2, temp)

    def read_temp(self):
        status = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_STATUS_REG)

        if not status & 0x01:
            return 'Temperature not available.'

        temp = self.bus.read_i2c_block_data(
            LPS25H_ADDRESS, LPS25H_TEMP_OUT_L | 0x80, 2)

        temp = twos_complement(
            bin_str(((temp[1] << 8) | temp[0]), 16), 16) / 480 + 42.5

        return temp

    def read_pressure(self):
        status = self.bus.read_byte_data(LPS25H_ADDRESS, LPS25H_STATUS_REG)

        if not status & 0x02:
            return 'Pressure not available.'

        pressure = self.bus.read_i2c_block_data(
            LPS25H_ADDRESS, LPS25H_PRESS_POUT_XL | 0x80, 3)

        pressure = twos_complement(bin_str(
            ((pressure[2] << 16) | (pressure[1] << 8) | pressure[0]), 24), 24) / 4096

        return pressure
