---
globs: ["**/module.py", "**/module*.py", "**/connection*.py"]
---

# Module Rules

- Streams are declared as type annotations: `color_image: In[Image]`, `processed: Out[Image]`
- `Module.__init__` auto-instantiates streams from type annotations
- `@rpc` on `start()` and `stop()` — these are lifecycle hooks
- Blueprint factory: `my_module = MyModule.blueprint` (a partial of `Blueprint.create`)
- Stream auto-connection: modules with matching `(name, type)` pairs (one `In`, one `Out`) connect automatically
- Use `.remappings()` to override stream name matching
- Custom transport: `blueprint.transports({("my_stream", MyType): SHMTransport(...)})` — use SHM for images/pointclouds
