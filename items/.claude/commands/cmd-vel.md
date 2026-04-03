Send a velocity command to the running robot via LCM.

Parse the user's intent into linear_x, linear_y, and angular_z values, then run:

```
source .venv/bin/activate && python bin/send_cmd_vel <linear_x> <linear_y> <angular_z>
```

Guidelines:
- "forward" → positive linear_x (e.g. 0.5)
- "backward" → negative linear_x (e.g. -0.5)
- "left" (strafe) → positive linear_y (e.g. 0.5)
- "right" (strafe) → negative linear_y (e.g. -0.5)
- "turn left" → positive angular_z (e.g. 0.5)
- "turn right" → negative angular_z (e.g. -0.5)
- "stop" → 0 0 0
- Default speed is 0.5 m/s unless the user specifies otherwise
- If the user says just "cmd-vel" with no arguments, send stop (0 0 0)
