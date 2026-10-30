---
title: "Custom ESP32 Development Board"
doc: AN-004
date: 2026-02-01
period: Feb 2026
role: Personal project
context: Personal
summary: A 2-layer ESP32-S3 development board taken from component selection to bring-up, with a USB-C port, a matched USB differential pair and protection circuitry.
tags: [pcb, esp32, fusion 360]
image: /assets/img/esp32-devboard.jpg
image_alt: "The finished red 2-layer development board held in hand, with an ESP32-S3-WROOM-1 module, USB-C connector, BOOT and RESET buttons, an RGB LED and labeled pin headers down both sides"
image_caption: Finished board
image_ratio: 0.75
images:
  - src: /assets/img/esp32-devboard-bringup.jpg
    ratio: 1.098
    alt: "The half-soldered board plugged into a laptop over USB-C, with its red power LED on and a terminal behind it printing 'alive 91 s' through 'alive 95 s' after a successful PlatformIO upload"
    caption: First upload, half soldered
---

I wanted to design a board entirely on my own, from picking parts to getting code running on it, so I made my own ESP32 dev board. It's a 2-layer board designed in Fusion 360 around an ESP32-S3-WROOM-1 module, with the pins broken out to labeled headers down both sides.

Power and data come in over USB-C, with the two 5.1&nbsp;kΩ resistors USB-C needs before it'll supply power. I routed the USB data lines as a matched differential pair, put decoupling caps right at the module, stitched the ground with vias, and added reverse-polarity and ESD protection so one mistake wouldn't kill it. BOOT and RESET buttons, an RGB LED and a power LED round it out.

I didn't wait until it was fully assembled to test it. With the headers and RESET button still missing, I plugged it in, uploaded a test program and watched it print "alive" every second over serial. That meant the power, USB and module were all working.
