---
title: "FPGA–STM32 UART Loop"
doc: AN-005
date: 2026-10-01
period: Oct 2026
role: Personal project
context: Personal
summary: A three-device UART loop between a PC, a Tang Nano 20K FPGA and an STM32, with UART modules written in Verilog and every byte checked end to end.
tags: [fpga, verilog, stm32, uart, python]
---

## Overview

A three-device UART loop between a PC, a Tang Nano 20K FPGA and an STM32. Test data leaves the PC, passes through the FPGA and the STM32, and comes back to the PC, where a script checks that every byte survived the trip. It's my first FPGA project, and a step on from the [bare-metal STM32 acquisition system]({{ '/projects/stm32-daq/' | relative_url }}).

<!-- TODO: link the repo here, e.g.
Source code: [github.com/25liujustin1/REPO-NAME](https://github.com/25liujustin1/REPO-NAME)
-->

## Signal Path

1. The PC sends test data to the FPGA through the board's USB-serial interface.
2. A Verilog UART receiver on the FPGA captures each byte, and a UART transmitter forwards it to the STM32.
3. The STM32 receives the data on one USART and relays it back to the PC on a second USART, connected through the ST-LINK.
4. A Python script compares the data sent and received to check for dropped or corrupted bytes.

## FPGA UART in Verilog

- Baud-rate generator
- Receive and transmit state machines
- Input synchronizer on the RX line, so the asynchronous serial input can't cause metastability

## Verification

- Each UART module is verified in simulation before it goes on hardware.
- On hardware, the Python script checks the full chain end to end.

## Key Specifications

| Parameter | Value |
|---|---|
| FPGA | Tang Nano 20K (Gowin GW2AR-18) |
| MCU | STM32 |
| HDL | Verilog |
| Links | 3 UART hops: PC → FPGA → STM32 → PC |
| Host software | Python |
