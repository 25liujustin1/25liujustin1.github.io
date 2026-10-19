---
title: "Vitagotchi"
doc: AN-002
order: 2
date: 2026-04-01
period: Apr 2026
role: UCLA IdeaHacks 2026 (36 hours, team of 4)
context: Hackathon
summary: A two-ESP32 wearable that classifies health state in real time, plus a plush desktop companion with OLED displays and LLM-generated responses.
tags: [esp32, wearable, hackathon, power]
---

## Overview

Vitagotchi was built in 36 hours at UCLA IdeaHacks 2026 with a team of four. It pairs a wearable that tracks health signals with a desktop companion that reacts to them.

<!-- TODO: add a photo or demo video, e.g.
![Vitagotchi plush and wearable](/assets/img/vitagotchi.jpg)
-->

## Wearable

- Two ESP32s classify health state in real time from accelerometer, heart rate, and temperature/humidity data.
- ESP-NOW handles the wireless link between devices.
- Data is logged to Firebase and shown on a web dashboard.

## Desktop Companion

- An interactive plush form factor.
- Dual OLED displays, an RGB LED and flex sensors.
- LLM-generated responses for real-time, multimodal interaction with the user.

## Power and Prototyping

- Built portable power systems with boost and LDO regulation.
- Rapidly prototyped the hardware on perfboard.

## Key Specifications

| Parameter | Value |
|---|---|
| Build time | 36 hours |
| Team | 4 people |
| MCUs | 2 × ESP32 |
| Wireless | ESP-NOW |
| Backend | Firebase + web dashboard |
