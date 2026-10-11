---
title: "Custom ESP32 Development Board"
doc: AN-004
order: 4
date: 2026-02-01
period: Feb 2026
role: Personal project
summary: A 2-layer ESP32 development board taken from component selection to bring-up, with a matched USB differential pair and protection circuitry.
tags: [pcb, esp32, usb]
---

## Overview

A 2-layer ESP32 development board that I designed and routed myself, from choosing components to bringing up the finished board.

<!-- TODO: add a 3D render or photo, e.g.
![ESP32 dev board](/assets/img/esp32-devboard.jpg)
-->

## Layout

- Routed USB D+/D− as a matched differential pair.
- Placed decoupling capacitors at the ESP32's power pins.
- Added ground stitching vias.

## Features and Protection

- External BOOT and RESET switches.
- Reverse-polarity protection.
- ESD protection.

## Key Specifications

| Parameter | Value |
|---|---|
| Layers | 2 |
| MCU | ESP32 |
| USB | Matched differential pair |
| Protection | Reverse polarity, ESD |
