import time
import random
import board
import busio
import adafruit_lps2x
import adafruit_hts221
import adafruit_lsm9ds1


# DPAD and LED code ported from 
# https://github.com/4eMaLo/SenseHAT-Game-of-Life/blob/master/sense_hat.py
# by John Doe (@4eMaLo)

class DPad:
    def __init__(self, i2c, address=0x46):
        self.ctrl_address = address
        self.buffer = bytearray(2)
        self.i2cbus = i2c

    def get_state(self):
        while not self.i2cbus.try_lock():
            pass
        self.buffer[1]=0xF2
        self.i2cbus.writeto_then_readfrom(self.ctrl_address,self.buffer,self.buffer,out_start=1,in_start=1)
        self.i2cbus.unlock()
        joy=self.buffer[1]
        down = joy & 1 != 0
        right = joy & 0b10 != 0
        up = joy & 0b100 != 0
        left = joy & 0b10000 != 0
        push = joy & 0b1000 != 0

        return up, down, left, right, push

class LedMatrix:
    framebuffer = [0x00] * 192

    def __init__(self, i2c, address=0x46):
        self.ctrl_address = address
        self.i2cbus = i2c
        self.buffer = bytearray(2)

    def clear(self):
        i = 0
        while i < 192:
            self.write_byte(i, 0)
            i += 1
        return False

    def set_pixel_fb(self, x, y, color):
        self.framebuffer[x*24+y   ] = color[0]
        self.framebuffer[x*24+y+8 ] = color[1]
        self.framebuffer[x*24+y+16] = color[2]
        return False

    def set_pixel_raw(self, x,y, color):
        ''' Color is in the form ( RED, GREEN, BLUE ), where each value x is 0 <= x < 64 '''
        i = 0
        while not self.i2cbus.try_lock():
            pass
        self.buffer[0]= x*24+y
        self.buffer[1]=color[0]
        self.i2cbus.writeto(self.ctrl_address, self.buffer, start=0)
        self.buffer[0]= x*24+y+8
        self.buffer[1]=color[1]
        self.i2cbus.writeto(self.ctrl_address, self.buffer, start=0)
        self.buffer[0]= x*24+y+16
        self.buffer[1]=color[2]
        self.i2cbus.writeto(self.ctrl_address, self.buffer, start=0)
        self.i2cbus.unlock()
        return False

    def fb_flush(self):
        i = 0
        while not self.i2cbus.try_lock():
            pass
        while i < 192:
            self.buffer[0]=i
            self.buffer[1]=self.framebuffer[i]
            self.i2cbus.writeto(self.ctrl_address, self.buffer, start=0)
            i += 1
        self.i2cbus.unlock()
        return False


    def write_byte(self, addr, data):
        while not self.i2cbus.try_lock():
            pass
        self.buffer[0]=addr
        self.buffer[1]=data
        self.i2cbus.writeto(self.ctrl_address, self.buffer, start=0)
        self.i2cbus.unlock()
        return False

    def read_byte(self, addr):
        while not self.i2cbus.try_lock():
            pass
        self.i2cbus.readfrom_into(self.ctrl_address, addr,self.buffer, start=1)
        self.i2cbus.unlock()
        return self.buffer[1]


lps25h_addr = 0x5c
lsm9ds1_mag_addr = 0x1c
hts221_addr = 0x5f # Matches Adafruit breakout and library - here for reference
led2472g_addr = 0x46
lsm9ds1_xg_addr = 0x6a

i2c=busio.I2C(board.GP21,board.GP20)
lps25h=adafruit_lps2x.LPS25(i2c,lps25h_addr)
hts221=adafruit_hts221.HTS221(i2c)
lsm9ds1=adafruit_lsm9ds1.LSM9DS1_I2C(i2c,lsm9ds1_mag_addr,lsm9ds1_xg_addr)

dpad=DPad(i2c)
leds=LedMatrix(i2c)

leds.clear()

i=0

while True:
    print("LPS25H")
    print("Pressure: %.2f hPa" % lps25h.pressure)
    print("Temperature: %.2f C" % lps25h.temperature)
    print()
    print("HTS221")
    print("Relative Humidity: %.2f %% rH" % hts221.relative_humidity)
    print("HTS Temperature: %.2f C" % hts221.temperature)

    accel_x, accel_y, accel_z = lsm9ds1.acceleration
    mag_x, mag_y, mag_z = lsm9ds1.magnetic
    gyro_x, gyro_y, gyro_z = lsm9ds1.gyro
    temp = lsm9ds1.temperature
    print()
    print("LSM9DS1")
    print(
        "Acceleration (m/s^2): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
            accel_x, accel_y, accel_z
        )
    )
    print(
        "Magnetometer (gauss): ({0:0.3f},{1:0.3f},{2:0.3f})".format(mag_x, mag_y, mag_z)
    )
    print(
        "Gyroscope (degrees/sec): ({0:0.3f},{1:0.3f},{2:0.3f})".format(
            gyro_x, gyro_y, gyro_z
        )
    )
    print("Temperature: {0:0.3f}C".format(temp))
    print()
    print("Stick")
    print(dpad.get_state())

    leds.set_pixel_raw(random.randint(0,7),random.randint(0,7),(random.randint(0,63),random.randint(0,63),random.randint(0,63)))
    time.sleep(1)