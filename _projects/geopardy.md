---
title: "Geopardy"
doc: AN-010
date: 2025-12-17
period: Dec 2025 – Jan 2026
role: Personal project
context: Personal
summary: A multiplayer, Jeopardy-style geography game where players race to click the named country on a world map, with live rooms, chat and a speed-based leaderboard.
tags: [javascript, node.js, socket.io, web]
image: /assets/img/geopardy.jpg
video: /assets/video/geopardy-gameplay.mp4
video_poster: /assets/img/geopardy-poster.jpg
image_alt: "A round of Geopardy. After a 3-2-1 countdown, country names like Nicaragua, Greece, Oman, Taiwan, Algeria and Somalia appear over the world map, each correct country turns dark green, a wrong guess triggers a lockout countdown, and the leaderboard score climbs to 31"
image_caption: A round of Geopardy
---

Geopardy is a geography game I made over winter break. Everyone joins a room, the game calls out a country, and whoever clicks it on the map first gets the points.

The map has over 200 clickable countries and territories, and the really tiny island nations get circles around them so you can actually hit them. Faster answers are worth more, with 10 points within 2 seconds, 7 within 4, and 5 after that. Guess wrong and you're locked out for 2 seconds, so you can't just spam-click your way across Europe. Once every country has been called, the game names a winner and the host can start another round.

It runs on a Node.js server with Express and Socket.io. Every game gets its own room with a random six-character code, so multiple groups can play at once. The server picks countries without repeats, keeps score, updates the leaderboard live and runs the chat. If the host leaves, someone else becomes host instead of the game just dying.

You can play it at [geopardy-quiz.onrender.com](https://geopardy-quiz.onrender.com/). It's on Render's free tier, so the first load can take up to a minute while the server wakes up.

The source code is at [github.com/25liujustin1/geopardy](https://github.com/25liujustin1/geopardy).
