---
title: "Vitagotchi"
doc: AN-002
date: 2026-04-01
period: Apr 2026
role: UCLA IdeaHacks 2026 (36 hours, team of 4)
context: Hackathon
summary: A two-ESP32 wearable that classifies health state in real time, plus a plush desktop companion with OLED displays and LLM-generated responses.
tags: [esp32, wearable, hackathon]
image: /assets/img/vitagotchi.jpg
image_alt: "The Vitagotchi desktop companion, a tiger plush with an OLED display and ESP32 on its head and a second OLED display held in its paws"
---

Vitagotchi was my team's project for UCLA IdeaHacks 2026, built in 36 hours. Think Tamagotchi, but it reacts to your actual health.

There are two parts. The wearable is two ESP32s reading an accelerometer, a heart rate sensor and a temperature/humidity sensor, and figuring out your health state in real time. The two boards talk to each other over ESP-NOW, and everything gets logged to Firebase and shown on a web dashboard.

The other part is the tiger in the photo, which I designed. It has two OLED screens, an RGB LED, flex sensors and LLM-generated responses, so it actually talks back to you.

I also built the power system. Everything runs off a 1S LiPo, which we boost up and then buck back down. With only 36 hours, all of the hardware ended up on perfboard.
