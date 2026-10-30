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
image_alt: "Geopardy in a browser: a clickable world map with the United States highlighted green, a leaderboard label, and a sidebar with a Start Game button, the room code and a chat log"
---

Geopardy is a geography game I built over winter break for playing with friends. Everyone joins the same room, the game calls out a country, and the first player to find it on the world map and click it gets the points.

The map is an SVG with over 200 clickable countries and territories. Tiny island nations that would be impossible to hit get circular targets around them. Speed matters: a correct click within 2 seconds is worth 10 points, within 4 seconds 7, and after that 5. A wrong guess flashes red and locks you out for 2 seconds, so spamming clicks doesn't pay. Once every country has been called, the game announces the winner and the host can start a new round.

Behind it is a Node.js server using Express and Socket.io. Each game lives in its own room with a random six-character code, so several groups can play at once. The server picks countries without repeats, keeps everyone's score and pushes leaderboard updates live, and runs the room's chat. If the host leaves, it hands host controls to the next player instead of ending the game.

Play it: [geopardy-quiz.onrender.com](https://geopardy-quiz.onrender.com/) (hosted on Render's free tier, so the first load can take up to a minute while the server wakes up)

Source code: [github.com/25liujustin1/geopardy](https://github.com/25liujustin1/geopardy)
