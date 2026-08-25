Hardware Connected to RPi Pin Headers
=====================================

Urchin has two devices connected to pin headers:

* Alien Servo
* Eye LEDs

Both end up neing controlled using PWM.

Alien Servo
-----------

* 5V (pin 2)
* GND (pin 6)
* PWM0 (pin 12)

Eye LEDs
--------

* GND (pin 39)
* PWM1 (pin 35)


Raspberry Pi 3B Pinout
----------------------

```
  Used       Pin description   PH       PH   Pin description
             ---------------   --       --   --------------------
                        3.3V    1 □   □ 2    5V
              GPIO8/I2C-SDA1    3 □   ■ 4    5V
              GPIO9/I2C-SCL1    5 □   ■ 6    GND
                GPIO7/GPCLK0    7 □   □ 8    GPIO15
                         GND    9 □   □ 10   GPIO16
                       GPIO0   11 □   ■ 12   GPIO1/PWM0
                       GPIO2   13 □   □ 14   GND
                       GPIO3   15 □   □ 16   GPIO4
                        3.3V   17 □   □ 18   GPIO4
             GPIO12/SPI-MOSI   19 □   □ 20   GND
             GPIO13/SPI-MISO   21 □   □ 22   GPIO6
             GPIO14/SPI-SCLK   23 □   □ 24   GPIO10/SPI-CE0
                         GND   25 □   □ 26   GPIO11/SPI-CE1
          SDA0/I2C-ID-EEPROM   27 □   □ 28   GPIO31/I2C-ID-EEPROM
               GPIO21/GPCLK1   29 □   □ 30   GND
               GPIO22/GPCLK2   31 □   □ 32   GPIO26/PWM0
                 GPIO23/PWM1   33 □   □ 34   GND
          GPIO24/PCM_FS/PWM1   35 ■   □ 36   GPIO27
                      GPIO25   37 □   □ 38   GPIO28/PCM-DIN
                         GND   39 ■   □ 40   GPIO/PCM-DOUT
```

