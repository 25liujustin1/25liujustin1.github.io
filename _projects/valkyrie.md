---
title: "Valkyrie Rocket Avionics"
doc: AN-001
order: 1
date: 2025-11-01
period: Nov 2025 – Jun 2026
role: Avionics team member, UCLA Rocket Project
context: Team
summary: Multiple 4-layer ESP32 avionics PCBs with LoRa telemetry, GPS, IMU and dual altimeters for a hybrid rocket that reached ~13,400 ft.
tags: [pcb, power, rocketry, esp32]
---

## Overview

Valkyrie is a hybrid rocket built by the UCLA Rocket Project. I worked on the avionics team, which designs the flight electronics: the boards that track the rocket's position and altitude and send telemetry back to the ground. The vehicle reached an apogee of about 13,400&nbsp;ft.

<!-- TODO: add a photo of the boards, e.g.
![Valkyrie avionics boards](/assets/img/valkyrie-boards.jpg)
-->

## Avionics Boards

I contributed to the design of multiple 4-layer ESP32-based avionics PCBs featuring:

- LoRa telemetry
- GPS
- IMU
- Dual altimeters

I also assisted with hardware bring-up.

## Power System

I helped design and validate the power system for a bodytube PCB:

- Cascaded buck-LDO regulation
- Ideal-diode ORing for seamless switching between USB and battery power

## Assembly and Rework

- Soldered and assembled avionics hardware.
- Crimped and soldered board-to-board cable connections for the avionics and EGSE (electrical ground support equipment) systems.
- Debugged and reworked boards to resolve electrical issues.

## Key Specifications

| Parameter | Value |
|---|---|
| Apogee | ~13,400 ft |
| Board stackup | 4 layers |
| MCU | ESP32 |
| Telemetry | LoRa |
| Sensors | GPS, IMU, dual altimeters |
