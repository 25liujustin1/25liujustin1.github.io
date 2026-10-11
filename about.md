---
layout: page
title: Specifications
kind: About
permalink: /about/
---

## Description

I'm studying for a B.S. in Electrical Engineering at UCLA (expected June 2029). I do hardware research in two UCLA labs and worked on avionics for the UCLA Rocket Project. I like boards that have to work the first time: power, protection and bring-up.

## Absolute Maximum Ratings (Demonstrated)

| Parameter | MIN | MAX | UNIT |
|---|:-:|:-:|:-:|
| Continuous hackathon operation | | 36 | h |
| Cold plate temperature reached (Di Carlo Lab) | −8 | | °C |
| Rocket apogee supported (Valkyrie) | | ~13,400 | ft |
| PCB layer count | 2 | 4 | layers |
| ADC sample rate, bare-metal STM32 | | 1 | kHz |
| Team size | 2 | 10 | people |

<p class="note">Stresses beyond those listed may be possible but have not yet been tested.</p>

## Recommended Operating Conditions

| Parameter | Value |
|---|---|
| Field | Electrical Engineering (B.S.) |
| Graduation | June 2029 |
| Coursework | Signals and Systems; Computer Organization; Logic Design of Digital Systems |
| Location | Los Angeles, CA |

## Skills and Tools

| Category | Details |
|---|---|
| Technical | Multi-layer PCB design, power systems, bare-metal firmware, hardware integration, soldering |
| Languages | C/C++, Python, Verilog |
| Tools | KiCad, Autodesk (PCB/CAD), SolidWorks, LTspice, oscilloscope, Git |

## Detailed Description: Research

### Di Carlo Lab, California NanoSystems Institute · Aug 2026 – Present

- Designed and tuned an ESP32 PI control loop for a cold plate driven by 4 Peltier modules, integrated into eBot Bio's agentic AI platform for autonomous bioassays.
- Reworked the 3D-printed enclosure, taking the cold plate from 2&nbsp;°C down to −8&nbsp;°C.
- Built the power harness off a switching supply, with low-side MOSFET switching for the Peltier loads.

### Mechatronics and Controls Lab, UCLA MAE · Jun 2026 – Present

- Designed the main 2-layer PCB and pressure sensor board for a 6-DOF AUV, with cascaded buck-LDO regulation, fusing, ESD and P-channel MOSFET reverse-polarity protection, a 9-axis IMU and an ESP32–Raspberry Pi compute stack. Validated the power circuitry in LTspice.
- Worked with the mechanical and systems subteams on a 10-person team to integrate electronics into the vehicle, and co-owned the electrical BOM across motors, ESCs and batteries.
- Presented design updates and tradeoffs to non-electrical engineers at weekly electronics meetings.

## Qualification: Awards

- **4th Place, ACM AI Mini ML Challenge (UCLA) 2026.** Transfer-learning image classifier at 98.648% accuracy; 4th of 23 teams (team of 2, 8 hours).
- **"Most Slayful UI" (Best UI/UX), QWER Hacks 2026.** Full-stack LGBTQ event platform with web scraping and the Gemini API; chosen from 19 teams (team of 3, 24 hours).

## Revision History

| Date | Rev | Changes |
|---|:-:|---|
| Aug 2026 | D | Joined Di Carlo Lab (CNSI). |
| Jun 2026 | C | Joined Mechatronics and Controls Lab. |
| Apr 2026 | B | Shipped Vitagotchi at IdeaHacks. |
| Nov 2025 | A | Initial release. Joined UCLA Rocket Project avionics. |
