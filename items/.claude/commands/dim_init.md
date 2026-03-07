# DimOS Project Guide

Read this entire document before starting any work. This is your onboarding guide to the DimOS codebase.

---

## 1. Project Overview

DimOS is a modular robotics framework. The core abstractions are:

- **Module** - A unit of computation with typed input/output streams, RPCs, and skills
- **Blueprint** - An immutable, composable description of which modules to run and how to wire them
- **Stream** - Typed pub/sub channels (`In[T]` / `Out[T]`) connecting modules
- **Transport** - The wire protocol for streams (LCM multicast by default)
- **Spec** - Protocol interfaces that let modules reference each other by capability, not class

Key files:
| File | Purpose |
|------|---------|
| `dimos/core/module.py` | `ModuleBase` and `Module` base classes |
| `dimos/core/blueprints.py` | `Blueprint`, `_BlueprintAtom`, `autoconnect()` |
| `dimos/core/stream.py` | `In[T]`, `Out[T]`, `Transport[T]` |
| `dimos/core/transport.py` | `LCMTransport`, `pLCMTransport` |
| `dimos/core/module_coordinator.py` | `ModuleCoordinator` - orchestrates deploy + lifecycle |
| `dimos/core/worker.py` | Worker subprocess management, `Actor` proxy |
| `dimos/core/worker_manager.py` | Pool of worker processes |
| `dimos/core/docker_runner.py` | `DockerModule`, `StandaloneModuleRunner` |
| `dimos/core/rpc_client.py` | `RpcCall`, `RPCClient`, `ModuleProxyProtocol` |
| `dimos/core/core.py` | `@rpc` decorator |
| `dimos/agents/annotation.py` | `@skill` decorator |
| `dimos/spec/utils.py` | Spec protocol utilities |
| `dimos/robot/all_blueprints.py` | Auto-generated registry of all blueprints/modules |
| `dimos/robot/get_all_blueprints.py` | Runtime blueprint loader |
| `dimos/utils/data.py` | `get_data()` LFS helper, `LfsPath` |

---

## 2. Blueprint Build Timeline

When you call `blueprint.build()` (`dimos/core/blueprints.py:496`), here is the exact sequence of operations. Each step notes where code executes: **HOST** (the main orchestrating process), **WORKER** (a forked subprocess), or **DOCKER** (a separate container).

### Phase 1: Configuration (HOST)

```
blueprint.build(cli_config_overrides)
  |
  +-- [HOST] global_config.update(**self.global_config_overrides)    # line 501
  +-- [HOST] global_config.update(**cli_config_overrides)            # line 502-503
```

### Phase 2: Validation (HOST)

```
  +-- [HOST] self._run_configurators()        # line 505 (blueprints.py:230-243)
  |     Runs SystemConfigurator instances (e.g., clock sync setup).
  |     Exits if user declines.
  |
  +-- [HOST] self._check_requirements()       # line 506 (blueprints.py:245-258)
  |     Runs callable checks. Exits on failure.
  |
  +-- [HOST] self._verify_no_name_conflicts() # line 507 (blueprints.py:260-293)
        Validates no two streams share a name with different types.
        Applies remappings during validation.
```

### Phase 3: Start Worker Pool (HOST)

```
  +-- [HOST] module_coordinator = ModuleCoordinator(cfg=global_config)  # line 510
  +-- [HOST] module_coordinator.start()                                  # line 511
        |
        +-- [HOST] WorkerManager(n_workers=N).start()
              Spawns N worker subprocesses using forkserver context.
              Each worker runs _worker_entrypoint() -> _worker_loop().
```

### Phase 4: Deploy Modules (HOST -> WORKER or DOCKER)

```
  +-- [HOST] self._deploy_all_modules(module_coordinator, global_config)  # line 514
        |     (blueprints.py:295-305)
        |     Constructs init kwargs for each _BlueprintAtom.
        |     Calls module_coordinator.deploy_parallel(module_specs).
        |
        +-- [HOST] module_coordinator.deploy_parallel()  # (module_coordinator.py:94-133)
              |
              |  Splits specs into docker_specs vs worker_specs.
              |
              +-- For WORKER modules:
              |     [HOST] WorkerManager.deploy_parallel(worker_specs)
              |       -> [HOST] Sends "deploy_module" message via pipe to worker subprocess
              |       -> [WORKER] _worker_loop receives message
              |       -> [WORKER] Module.__init__() runs:
              |            - Creates In[T]/Out[T] stream instances from type annotations
              |            - Calls ModuleBase.__init__():
              |              - Creates event loop + thread
              |              - Instantiates RPC transport (LCMRPC)
              |              - Calls rpc.serve_module_rpc(self) - registers all @rpc methods
              |              - Calls rpc.start()
              |       -> [HOST] Returns Actor proxy (MethodCallProxy)
              |
              +-- For DOCKER modules:
                    [HOST] DockerWorkerManager.deploy_parallel(docker_specs)
                      -> [HOST] DockerModule.__init__():
                           - Builds/pulls Docker image if needed
                           - Runs `docker run -d --network=host ...` with JSON payload
                      -> [DOCKER] Container starts, runs StandaloneModuleRunner
                           - Dynamically imports module class
                           - Calls Module.__init__() (same as worker but inside container)
                           - RPC server starts on LCM multicast
                      -> [HOST] _wait_for_rpc() polls until container's RPC is reachable
```

### Phase 5: Connect Streams (HOST -> WORKER/DOCKER via RPC)

```
  +-- [HOST] self._connect_streams(module_coordinator)  # line 515
        |     (blueprints.py:308-334)
        |
        |  Groups streams by (remapped_name, type).
        |  For each unique (name, type):
        |    - Chooses transport: LCMTransport (if type has lcm_encode),
        |      pLCMTransport (pickle fallback), or custom from transport_map
        |    - For each module with a matching stream:
        +------ [HOST->WORKER/DOCKER RPC] instance.set_transport(stream_name, transport)
                  -> [WORKER/DOCKER] Module.set_transport() stores transport on stream object
                  -> Stream.publish() now broadcasts via LCM multicast
                  -> Stream.subscribe() now receives via LCM multicast
```

### Phase 6: Connect RPCs (HOST -> WORKER/DOCKER via RPC)

```
  +-- [HOST] self._connect_rpc_methods(module_coordinator)  # line 516
        |     (blueprints.py:418-494)
        |
        |  Gathers all @rpc methods from all deployed modules.
        |  Registers methods under class name + interface names.
        |  For modules that declared rpc_calls or set_X methods:
        +------ [HOST->WORKER/DOCKER RPC] set_rpc_method(name, callable)
                  Injects RPC callable from one module into another.
```

### Phase 7: Connect Module References (HOST -> WORKER/DOCKER via RPC)

```
  +-- [HOST] self._connect_module_refs(module_coordinator)  # line 517
        |     (blueprints.py:336-416)
        |
        |  For each ModuleRef (declared as type annotation on a module):
        |    - Finds deployed module matching the Spec (structural + annotation check)
        |    - Handles ambiguity (error if multiple match)
        +------ [HOST->WORKER/DOCKER RPC] set_module_ref(name, rpc_client)
                  Sets the reference so the requesting module can call RPCs on the target.
```

### Phase 8: Start All Modules (HOST -> WORKER/DOCKER via RPC)

```
  +-- [HOST] module_coordinator.start_all_modules()  # line 519
        |     (module_coordinator.py:135-144)
        |
        |  For each deployed module (in parallel via ThreadPoolExecutor):
        +------ [HOST->WORKER/DOCKER RPC] module.start()
        |         -> [WORKER/DOCKER] Module.start() runs user-defined startup logic
        |
        |  Then for each module that has on_system_modules():
        +------ [HOST->WORKER/DOCKER RPC] module.on_system_modules(all_modules)
```

### Phase 9: Return (HOST)

```
  +-- [HOST] return module_coordinator
        Caller uses module_coordinator.loop() to block,
        or module_coordinator.stop() to shut down.
```

---

## 3. What Is a Blueprint?

A `Blueprint` (`dimos/core/blueprints.py:112`) is a **frozen dataclass** describing a system of modules to deploy. It contains:

- `blueprints: tuple[_BlueprintAtom, ...]` - The modules and their constructor args
- `transport_map` - Custom transports for specific streams
- `global_config_overrides` - Config like `n_workers`, `robot_model`
- `remapping_map` - Stream/module-ref renaming rules
- `requirement_checks` - Pre-flight validation functions
- `configurator_checks` - System configurator instances

Blueprints are **immutable** - every configuration method returns a new Blueprint:
```python
bp = (
    autoconnect(module_a(), module_b())
    .global_config(n_workers=4, robot_model="go2")
    .transports({("joint_state", JointState): LCMTransport("/js", JointState)})
    .requirements(check_network)
    .configurators(ClockSyncConfigurator())
)
```

`autoconnect(*blueprints)` merges multiple blueprints, deduplicating modules (last wins).

---

## 4. How all_blueprints.py Works

`dimos/robot/all_blueprints.py` is an **auto-generated** registry mapping CLI names to blueprint/module import paths. It has two dicts:

```python
all_blueprints = {
    "unitree-go2": "dimos.robot.unitree.go2.blueprints.smart.unitree_go2:unitree_go2",
    "arm-teleop": "dimos.teleop.quest.blueprints:arm_teleop",
    # ~89 entries
}

all_modules = {
    "agent": "dimos.agents.agent",
    "camera-module": "dimos.hardware.sensors.camera.module",
    # ~54 entries
}
```

**Generation:** `dimos/robot/test_all_blueprints_generation.py` scans all `.py` files via AST, detecting:
- `autoconnect()` calls
- Blueprint method chains (`.transports()`, `.global_config()`, etc.)
- `SomeModule.blueprint` factory calls

Variable names are converted to CLI names (`_` -> `-`).

**Loading at runtime:** `dimos/robot/get_all_blueprints.py`:
```python
def get_blueprint_by_name(name: str) -> Blueprint:
    module_path, attr = all_blueprints[name].split(":")
    module = __import__(module_path, fromlist=[attr])
    return getattr(module, attr)
```

---

## 5. How to Add a New Blueprint

1. Create a file in the appropriate domain directory (e.g., `dimos/robot/myrobot/blueprints.py`)
2. Import modules and compose with `autoconnect`:

```python
from dimos.core.blueprints import autoconnect
from dimos.hardware.sensors.camera.module import camera_module
from dimos.robot.myrobot.connection import myrobot_connection

myrobot_basic = autoconnect(
    myrobot_connection(),
    camera_module(),
).global_config(n_workers=3, robot_model="myrobot")
```

3. Run the blueprint generation test/script to update `all_blueprints.py`, or manually add an entry.

**Convention:** The top-level variable name becomes the CLI name (`myrobot_basic` -> `myrobot-basic`).

---

## 6. How to Add a New Robot

A robot is a **Module** that implements hardware communication. Typical pattern:

```python
# dimos/robot/myrobot/connection.py

@dataclass
class MyRobotConfig(ModuleConfig):
    ip_address: str = "192.168.1.100"
    control_rate: float = 50.0

class MyRobotConnection(Module[MyRobotConfig]):
    # Declare streams as type annotations
    cmd_vel: In[Twist]           # receives velocity commands
    color_image: Out[Image]      # publishes camera frames
    odometry: Out[Odometry]      # publishes odometry

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Hardware-specific init

    @rpc
    def start(self) -> None:
        # Connect to robot, start streaming

    @rpc
    def stop(self) -> None:
        # Disconnect
        super().stop()

# Blueprint factory
myrobot_connection = MyRobotConnection.blueprint
```

Then create a blueprint file composing this with other modules (see section 5).

---

## 7. How to Add a New Sensor

Sensors follow the same Module pattern. Example camera sensor:

```python
# dimos/hardware/sensors/mysensor/module.py

@dataclass
class MySensorConfig(ModuleConfig):
    device_id: int = 0
    frequency: float = 30.0

class MySensorModule(Module[MySensorConfig]):
    readings: Out[SensorData]    # output stream

    @rpc
    def start(self) -> None:
        # Initialize hardware, start publishing to self.readings

# Blueprint factory
my_sensor = MySensorModule.blueprint
```

---

## 8. How Skills Work

Skills are module methods exposed to AI agents. They use a simple decorator:

```python
# dimos/agents/annotation.py
def skill(func):
    func.__rpc__ = True    # Also an RPC (callable remotely)
    func.__skill__ = True  # Discoverable by agents
    return func
```

**Usage in a module:**
```python
class MyModule(Module):
    @skill
    def take_a_picture(self) -> Image:
        return self._latest_image

    @skill
    def navigate_to(self, x: float, y: float) -> bool:
        # navigation logic
        return True
```

**Discovery:** `ModuleBase.get_skills()` (an RPC method at `module.py:376-387`) introspects all methods with `__skill__=True`, extracts their JSON schema via langchain's `tool()`, and returns `list[SkillInfo]`.

**Existing skill containers:**
- `dimos/agents/skills/navigation.py` - `NavigationSkillContainer` (tag_location, navigate_with_text, stop_navigation)
- `dimos/agents/skills/demo_calculator_skill.py` - `DemoCalculatorSkill`
- `dimos/manipulation/pick_and_place_module.py` - Pick-and-place skills

---

## 9. How to Add a Stream to a Module

Streams are declared as **type annotations** on the Module class. The `Module.__init__` method automatically instantiates them.

```python
class MyModule(Module):
    # Input - receives data from other modules
    sensor_data: In[PointCloud2]

    # Output - publishes data to other modules
    processed_result: Out[CostMap]

    @rpc
    def start(self) -> None:
        # Subscribe to input
        self.sensor_data.subscribe(self._on_sensor_data)

    def _on_sensor_data(self, data: PointCloud2) -> None:
        result = self.process(data)
        # Publish to output
        self.processed_result.publish(result)
```

**Stream auto-connection:** When two modules in the same blueprint have streams with the **same name and type** (one `In`, one `Out`), they are automatically connected via a shared transport during `_connect_streams()`. To override names, use `.remappings()`.

**Custom transport:**
```python
blueprint.transports({
    ("my_stream", MyType): LCMTransport("/custom/channel", MyType),
})
```

---

## 10. How to Add an RPC to a Module

RPCs are methods decorated with `@rpc` that can be called remotely (from host or other modules):

```python
from dimos.core.core import rpc

class MyModule(Module):
    @rpc
    def get_status(self) -> dict:
        return {"running": True, "count": self._count}

    @rpc
    def set_parameter(self, name: str, value: float) -> bool:
        self._params[name] = value
        return True
```

RPCs are automatically discovered and served. Other modules can call them via:
- Module references (Spec-based linking)
- `rpc_calls` list + `set_X` injection pattern
- Direct `RPCClient` if you have the proxy

**`start()` and `stop()` are already RPCs** on `ModuleBase`. Override them for lifecycle hooks.

---

## 11. Available Utilities

### `get_data(name)` - LFS Data Helper
**File:** `dimos/utils/data.py:214`

Downloads data from Git LFS on demand. Data lives in `tests/data/`.

```python
from dimos.utils.data import get_data, LfsPath

# Simple file
path = get_data("sample.bin")

# Nested path in archive (auto-decompresses tar.gz)
frame = get_data("dataset/frames/001.png")

# Lazy-loading path (downloads only when accessed)
lazy = LfsPath("my_model_weights")
```

### Other Utilities

| File | Contents |
|------|----------|
| `dimos/utils/logging_config.py` | `setup_logger()` - structured logging via structlog |
| `dimos/utils/reactive.py` | RxPY helpers: `backpressure()`, reactive stream operators |
| `dimos/utils/transform_utils.py` | Coordinate transform utilities |
| `dimos/utils/trigonometry.py` | Trig helpers for robotics |
| `dimos/utils/gpu_utils.py` | GPU detection and management |
| `dimos/utils/urdf.py` | URDF parsing utilities |
| `dimos/utils/path_utils.py` | Path manipulation helpers |
| `dimos/utils/llm_utils.py` | LLM interaction utilities |
| `dimos/utils/generic.py` | Generic Python utilities |
| `dimos/utils/threadpool.py` | Thread pool helpers |
| `dimos/utils/sequential_ids.py` | Sequential ID generation |
| `dimos/utils/colors.py` | Terminal color utilities |
| `dimos/utils/human.py` | Human-readable formatting |
| `dimos/utils/metrics.py` | Performance metrics |
| `dimos/utils/safe_thread_map.py` | Thread-safe map operations |

---

## 12. Project Directory Structure

```
dimos/
  core/           # Framework core: Module, Blueprint, Stream, RPC, Worker, Docker
  agents/         # AI agent framework, @skill decorator, skill containers
  robot/          # Robot implementations (unitree go2/g1/h1, etc.)
    all_blueprints.py    # Auto-generated blueprint registry
    get_all_blueprints.py # Runtime loader
  hardware/       # Hardware drivers
    sensors/      # Camera, Lidar, IMU modules
  control/        # Control coordinator, joint management
  navigation/     # Path planning, exploration, costmaps
  mapping/        # Voxel mapping, cost mapping
  manipulation/   # Pick-and-place, grasp generation
  teleop/         # Teleoperation (phone, VR Quest)
  visualization/  # Rerun, Foxglove, web visualization
  protocol/       # RPC specs, pub/sub protocols
  spec/           # Spec protocol definitions (perception, navigation, etc.)
  types/          # Shared message types (Image, Twist, Odometry, etc.)
  skills/         # Legacy skill library (deprecated - use @skill on modules instead)
  utils/          # Utilities (data, logging, transforms, GPU, etc.)
tests/
  data/           # LFS test data (accessed via get_data())
```

---

## 13. Quick Reference: Common Patterns

**Creating a module blueprint factory:**
```python
# At module level, after class definition:
my_module = MyModule.blueprint  # This is a partial of Blueprint.create
```

**Composing blueprints:**
```python
full_system = autoconnect(
    robot_connection(),
    camera_module(hardware=MyCamera),
    navigation_planner(),
    agent_module(),
).global_config(n_workers=5)
```

**Running a blueprint:**
```python
coordinator = full_system.build()
coordinator.loop()  # Blocks until Ctrl+C
```

**Docker modules:** Set `default_config` to a `DockerModuleConfig` subclass. The module will automatically be deployed in a container instead of a worker process.

**Stream remapping:**
```python
blueprint.remappings([
    (ModuleA, "color_image", "front_camera"),  # Rename stream
    (ModuleB, "camera_ref", SpecificCamera),   # Remap module ref
])
```

---

## 14. CLI and Daemon Mode

The DimOS CLI (`dimos/robot/cli/dimos.py`) provides lifecycle management via `typer`.

### Running a blueprint

```bash
# Foreground (blocks, Ctrl+C stops)
dimos run unitree-go2

# Background (daemon mode)
dimos run unitree-go2 --daemon
```

### Foreground mode
Calls `coordinator.loop()` which blocks on a `threading.Event`. Ctrl+C raises `KeyboardInterrupt`, and the `finally` block calls `coordinator.stop()` to tear down all modules.

### Daemon mode (`--daemon`)
1. **Health check** — verifies all worker processes are alive before detaching
2. **Prints status** — module/worker counts, run ID, log directory
3. **Double-fork daemonize** (`dimos/core/daemon.py`) — detaches from terminal via `os.setsid()`, redirects stdio to `/dev/null`. All logging goes through structlog's file handler to `<log_dir>/main.jsonl`
4. **Saves a `RunEntry`** to disk (`dimos/core/run_registry.py`) — records PID, blueprint name, timestamps, log dir
5. **Installs signal handlers** — SIGTERM/SIGINT trigger `coordinator.stop()`, then `entry.remove()`, then `sys.exit(0)`
6. **Enters `coordinator.loop()`** — blocks until a signal arrives

### Management commands

```bash
dimos status   # Show running instance (run ID, PID, uptime, log path)
dimos stop     # Send SIGTERM to the running instance
dimos stop -f  # Send SIGKILL (force kill)
```

### Shutdown paths summary

| Path | Trigger | Mechanism | File |
|------|---------|-----------|------|
| Foreground | Ctrl+C | `KeyboardInterrupt` → `finally: coordinator.stop()` | `module_coordinator.py:loop()` |
| Daemon | `dimos stop` / SIGTERM | Signal handler → `coordinator.stop()` | `daemon.py:install_signal_handlers()` |
| Signal handlers | SIGINT/SIGTERM | Installed in `coordinator.start()` → calls `self.stop()` | `module_coordinator.py:start()` |

`coordinator.stop()` iterates deployed modules in reverse order, calling `module.stop()` on each (including `DockerModule.stop()` which stops/removes containers), then closes all worker processes.
