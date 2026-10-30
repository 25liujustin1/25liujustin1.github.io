---
title: "Thrustworthy"
doc: AN-008
date: 2026-10-24
period: Oct 2026
role: Cal Hacks 2026 (36 hours, team of 4)
context: Hackathon
summary: A choking-response training mannequin with 9 force sensors that grades hand placement, timing and sequence of back blows, abdominal thrusts and CPR in real time.
tags: [esp32, sensors, typescript, react, hackathon]
image: /assets/img/thrustworthy.jpg
image_alt: "The Thrustworthy mannequin at Cal Hacks: a blindfolded torso with round force sensors taped to the chest and abdomen, wired down to an ESP32 on a breadboard at its base"
---

My team of four built Thrustworthy in 36 hours at Cal Hacks 2026: a training station that teaches adult choking response. You practice on the mannequin in the photo, and it coaches you through back blows, abdominal thrusts and CPR, following the AHA Adult Basic Life Support guidelines.

Nine force-sensitive resistors are taped across target and off-target spots on the front, back and sternum. An ESP32-S3 reads them and streams the readings over USB to a React/TypeScript web app, which works out where each hit landed, how sharp it was and whether it came in the right order, then tells you out loud what to fix.

My main piece was telling a real thrust from a slow push. We tested hits on the mannequin and found that proper thrusts rose from 10% to 90% of their peak force in 175–211&nbsp;ms, while slow pushes took 547–1272&nbsp;ms, so I used those measurements to set the cutoffs, along with checks for hits that come too fast or too far apart. I also turned raw sensor readings into an estimated force in newtons, using the voltage divider and the sensor's datasheet curve.

On the software side, I added the spoken instructions and a voice assistant you can ask questions by saying "Gemini, …", and made the app reconnect to the ESP32 on its own when it's plugged back in. My teammates wrote the firmware, the placement heatmap and the body and airway animations.
