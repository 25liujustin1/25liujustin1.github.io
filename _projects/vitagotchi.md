---
title: "Vitagotchi"
doc: AN-002
date: 2026-04-01
period: Apr 2026
role: UCLA IdeaHacks 2026 (36 hours, team of 4)
context: Hackathon
summary: A two-ESP32 wearable that classifies health state in real time, plus a plush desktop companion with OLED displays and LLM-generated responses.
tags: [esp32, wearable, hackathon, power]
image: /assets/img/vitagotchi.jpg
image_alt: "The Vitagotchi desktop companion: a tiger plush with an OLED display and ESP32 on its head and a second OLED display held in its paws"
---

My team of four built Vitagotchi in 36 hours at UCLA IdeaHacks 2026. The idea was a health tracker you'd actually want to check in on: instead of numbers on a screen, a plush companion on your desk that reacts to how you're doing.

It comes in two halves. The wearable uses two ESP32s to read an accelerometer, a heart rate sensor and a temperature/humidity sensor, and classifies your health state in real time. The two boards talk to each other wirelessly over ESP-NOW, and readings are logged to Firebase and shown on a web dashboard.

The other half is the companion, the tiger in the photo, which I designed. It has two OLED displays, an RGB LED and flex sensors, so it can show how you're doing and respond when you squeeze it, with LLM-generated replies that make it feel more like a pet than a gadget.

I also built the portable power for both halves, with boost and LDO regulation, and we prototyped all of the hardware on perfboard to make it in time.
