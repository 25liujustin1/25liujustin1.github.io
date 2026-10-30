---
title: "FPGA–STM32 UART Loop"
doc: AN-005
date: 2026-10-01
period: Oct 2026
role: Personal project (in progress)
context: Personal
summary: My first FPGA project, linking a Tang Nano 20K and an STM32 over UART with UART modules written in Verilog.
tags: [fpga, verilog, stm32, uart, python]
---

This page is still in progress, so check back soon for the full write-up.

It's my first FPGA project and a follow-up to my [bare-metal STM32 work]({{ '/projects/stm32-daq/' | relative_url }}). A Tang Nano 20K talks to an STM32 over UART, using receive and transmit modules I wrote in Verilog, each with its own baud-rate generator and state machine, plus a synchronizer on the receive line so the incoming signal can't cause metastability. I verified each module in simulation before putting it on hardware.
