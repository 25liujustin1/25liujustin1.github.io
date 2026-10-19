---
title: "Bare-Metal STM32 Signal Acquisition System"
doc: AN-003
order: 3
date: 2026-03-01
period: Mar 2026
role: Personal project
context: Personal
summary: Register-level STM32F446 drivers sampling the ADC at 1 kHz with timer-triggered DMA, streamed over UART to a Python plotter.
tags: [firmware, stm32, c, python]
---

## Overview

A signal acquisition system on the STM32F446, written without a HAL or vendor libraries. Every peripheral is configured through direct register access.

<!-- TODO: link the repo here, e.g.
Source code: [github.com/25liujustin1/REPO-NAME](https://github.com/25liujustin1/REPO-NAME)
-->

## Peripherals

Implemented directly through registers:

- GPIO
- UART
- Timers
- Interrupts

## Sampling Pipeline

- A timer triggers the ADC at 1&nbsp;kHz.
- DMA moves each sample into a 1000-sample buffer, so the CPU does very little work per sample.

## PC Visualization

- Samples stream over UART to a PC.
- A Python script plots the ADC readings in real time with Matplotlib.

<!-- TODO: add a screenshot of the Matplotlib plot, e.g.
![Live ADC plot](/assets/img/stm32-plot.png)
-->

## Key Specifications

| Parameter | Value |
|---|---|
| MCU | STM32F446 |
| Sample rate | 1 kHz |
| Buffer | 1000 samples (DMA) |
| Host link | UART |
| Host software | Python, Matplotlib |
