Send a navigation goal (clicked_point) to the running robot via LCM.

Parse the user's intent into x, y, and optionally z coordinates, then run:

```
source .venv/bin/activate && python bin/send_clicked_point <x> <y> [z]
```

Guidelines:
- If the user provides coordinates, use them directly
- z defaults to 0 if not specified
- Coordinates are in meters in the world/map frame
- If the user says just "goal" with no arguments, ask for coordinates
