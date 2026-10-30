---
title: "Bare-Metal STM32 Signal Acquisition System"
doc: AN-003
date: 2026-05-08
period: May 2026
role: Personal project
context: Personal
summary: Register-level STM32F446 firmware that streams ADC readings over UART to a live Python plot, using DMA and a double-buffered circular buffer.
tags: [firmware, stm32, c, python]
video: /assets/video/stm32-adc-live.mp4
video_poster: /assets/img/stm32-adc-live-poster.jpg
image_alt: "A live Matplotlib plot of ADC readings from 0 to 4095 over a 1000-sample window, rising and falling as a potentiometer is turned"
image_caption: Live plot while turning a potentiometer
---

I wanted to see what's actually going on under STM32's HAL libraries, so I set them aside and wrote firmware for an STM32F446 using just its registers. I went one peripheral at a time, starting with a blinking LED and moving through the SysTick timer, timer interrupts and a UART echo, then put it all together into a small data acquisition setup.

The first version just polls. It starts an ADC conversion, waits for it, prints the result over UART and repeats. It works, but the CPU spends basically all its time waiting. The second version hands that off to DMA. The ADC runs continuously, DMA copies every reading into a 1000-sample circular buffer on its own, and interrupts tell the CPU when each half fills up, so it can send one half over UART while DMA fills the other.

On my laptop, a Python script reads the serial data and plots the last 1000 samples live with Matplotlib, so turning a potentiometer moves the line in real time, like in the video.

One catch is that the ADC samples way faster than UART can send, so the plot shows snapshots instead of every sample. The next step is triggering the ADC from a timer at a rate the UART can actually keep up with.

The source code is at [github.com/25liujustin1/STM32-Baremetal](https://github.com/25liujustin1/STM32-Baremetal).
