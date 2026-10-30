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
image_alt: "The Thrustworthy mannequin at Cal Hacks, a blindfolded torso with round force sensors taped to the chest and abdomen, wired down to an ESP32 on a breadboard at its base"
---

Thrustworthy is a choking-response trainer my team of four built in 36 hours at Cal Hacks 2026. You practice back blows, abdominal thrusts and CPR on the mannequin in the photo, and it tells you out loud what you're doing wrong, based on the AHA's adult guidelines.

We taped nine force sensors across the front, back and sternum, some on the right spots and some just off them. An ESP32-S3 reads them and sends everything over USB to a React/TypeScript app, which works out where you hit, how hard and how sharply, and whether you did things in the right order.

My main job was telling a real thrust apart from a slow push. We hit the mannequin a bunch of times and found that good thrusts rose from 10% to 90% of their peak force in about 175–211&nbsp;ms, while slow pushes took 547–1272&nbsp;ms, so I used that to set the cutoffs. I also added checks for hits that come too fast or too far apart, and turned the raw readings into a rough force in newtons using the voltage divider and the sensor's datasheet curve.

On the software side, I added the spoken instructions and a voice assistant you can ask questions by saying "Gemini, …", and made the app reconnect to the ESP32 on its own when you plug it back in. My teammates handled the firmware, the heatmap and the animations.

There's more about the project on [Devpost](https://devpost.com/software/thrustworthy).
