---
title: "Custom ESP32 Development Board"
doc: AN-004
date: 2026-02-01
period: Feb 2026
role: Personal project
context: Personal
summary: A 2-layer ESP32-S3 development board taken from component selection to bring-up, with a USB-C port, a matched USB differential pair and protection circuitry.
tags: [pcb, esp32, usb]
image: /assets/img/esp32-devboard.jpg
image_alt: "The finished red 2-layer development board held in hand: an ESP32-S3-WROOM-1 module, USB-C connector, BOOT and RESET buttons, an RGB LED and labeled pin headers down both sides"
image_caption: Finished board
image_ratio: 0.75
images:
  - src: /assets/img/esp32-devboard-bringup.jpg
    ratio: 1.098
    alt: "The half-soldered board plugged into a laptop over USB-C, with its red power LED on and a terminal behind it printing 'alive 91 s' through 'alive 95 s' after a successful PlatformIO upload"
    caption: First upload, half soldered
---

This is the first development board I designed on my own, taking it all the way from choosing components to bringing up the finished board. It's built around an ESP32-S3-WROOM-1 module on a 2-layer PCB, with every usable pin broken out to labeled headers down both sides.

Power and data come in through a USB-C port, with the two 5.1&nbsp;kΩ resistors USB-C needs to request power. I routed the USB D+ and D− lines as a matched differential pair, placed decoupling capacitors at the module's power pins, and stitched the ground with vias. To keep the board safe from mistakes and static, it has reverse-polarity protection and ESD protection on the USB lines.

For flashing and debugging, BOOT and RESET buttons sit in the middle of the board, alongside an RGB LED for status and a red power LED.

I brought it up before it was fully assembled. With the headers and RESET button still missing, I plugged it in over USB-C, uploaded a test program from PlatformIO, and watched it print "alive" once a second over serial. That was the moment I knew the power, USB and module were all working.
