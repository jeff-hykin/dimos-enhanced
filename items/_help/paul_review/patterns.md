# Paul Nechifor's Code Review Patterns

*Auto-generated from 984 comments across 206 PRs*

---

## Overview Stats

| Metric | Count |
|--------|-------|
| Total comments | 984 |
| Inline code reviews | 874 |
| General PR comments | 97 |
| Review body comments | 13 |
| Comments with code suggestions | 74 |
| Questions asked | 222 |
| Direct imperatives | 10 |
| Positive feedback | 66 |

### Comment Length

| Metric | Value |
|--------|-------|
| Min | 3 chars |
| Max | 8257 chars |
| Median | 103 chars |
| Mean | 197 chars |

### Most Reviewed File Types

| Extension | Comments |
|-----------|----------|
| `.py` | 696 |
| `.md` | 94 |
| `(no ext)` | 27 |
| `.toml` | 16 |
| `.sh` | 13 |
| `.yml` | 5 |
| `.ts` | 5 |
| `.png` | 3 |
| `.lock` | 2 |
| `.dae` | 2 |
| `.json` | 2 |
| `.MD` | 1 |
| `.onnx` | 1 |
| `.pkl` | 1 |
| `.gz` | 1 |
| `.txt` | 1 |
| `.xml` | 1 |
| `.js` | 1 |
| `.dimos` | 1 |
| `.html` | 1 |

### Most Reviewed Files (Top 20)

| File | Comments |
|------|----------|
| `pyproject.toml` | 16 |
| `dimos/robot/cli/dimos.py` | 15 |
| `README.md` | 13 |
| `dimos/core/transport.py` | 12 |
| `dimos/robot/unitree/connection/go2.py` | 11 |
| `dimos/msgs/nav_msgs/OccupancyGrid.py` | 10 |
| `dimos/manipulation/manipulation_module.py` | 10 |
| `dimos/perception/temporal_memory.py` | 9 |
| `dimos/core/docker_module.py` | 9 |
| `dimos/protocol/pubsub/ddspubsub.py` | 9 |
| `dimos/control/coordinator.py` | 9 |
| `dimos/msgs/sensor_msgs/image_impls/CudaImage.py` | 8 |
| `docs/concepts/modules.md` | 8 |
| `dimos/core/worker.py` | 8 |
| `dimos/core/test_cli_stop_status.py` | 8 |
| `dimos/core/test_e2e_daemon.py` | 8 |
| `dimos/core/test_e2e_mcp_stress.py` | 8 |
| `dimos/msgs/sensor_msgs/Image.py` | 7 |
| `dimos/agents2/skills/interpret_map.py` | 7 |
| `dimos/dashboard/rerun_init.py` | 7 |

### Activity Over Time

| Month | Comments |
|-------|----------|
| 2025-08 | 15 |
| 2025-09 | 49 |
| 2025-10 | 77 |
| 2025-11 | 73 |
| 2025-12 | 151 |
| 2026-01 | 250 |
| 2026-02 | 209 |
| 2026-03 | 160 |

---

## Review Patterns by Category

### Suggestions (146 comments)

#### Code suggestions (74)

- **PR #1154** in `dimos/visualization/rerun/bridge.py`:
  > ```suggestion \n ```

- **PR #1436** in `dimos/core/test_daemon.py`:
  > ```suggestion \n ```

- **PR #1436** in `dimos/core/test_per_run_logs.py`:
  > ```suggestion \n ```

- **PR #829** in `docs/concepts/modules.md`:
  > ```suggestion \n - Detection (takes an image and a vision model like YOLO, outputs a stream of detections) \n ```

- **PR #1356** in `dimos/protocol/service/test_system_configurator.py`:
  > You can use the `mocker` fixture to not need to indent so much. It automatically cleans up when it's done. \n  \n ```suggestion \n     def test_handles_eof_error_on_input(self, mocker) -> None: \n         mocker.patch.dict(os.environ, {"CI": ""}, clear=False) \n         mock_check = MockConfigurator(passes=False) \n         mock_stdin = mocker.patch("sys.stdin") \n         mock_stdin.isatty.return...

#### Alternative approaches (45)

- **PR #918** in `dimos/manipulation/planning/world/drake_world.py`:
  > why not `setup_logger()`

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > Why Any instead of SportClient?

- **PR #1119** in `dimos/core/docker_module.py`:
  > Use an `Event()` instead of a boolean.

- **PR #955** in `dimos/models/vl/base.py`:
  > ~~Oh, I'm not saying you shouldn't have `query_multi_images`, just that it shouldn't have an implementation here and instead be an `@abstractmethod` like `query` is so that each actual model needs to implement it.~~ Oops, I was looking at an old version.

- **PR #1080**:
  > Personally, I don't like the API. It's similar to what we do with `LCM()` and others where we don't encode the lifecycle into the API. The API is simple, but doesn't give you enough control. \n  \n ## Sessions \n  \n ```python \n store = SqliteStore("recordings/lidar") \n store.save(data) \n ``` \n  \n Without a session, API calls race to create `self._conn`. You could add a lock. But it ...

#### Refactoring proposals (27)

- **PR #1042** in `dimos/agents/skills/person_follow.py`:
  > Extracted

- **PR #1114** in `dimos/protocol/pubsub/impl/lcmpubsub.py`:
  > Why an inline import?

- **PR #1119** in `dimos/core/docker_module.py`:
  > Why an inline import?

- **PR #1436** in `dimos/core/run_registry.py`:
  > We should rely on the `XDG_DATA_HOME` standard. This is used in `_get_user_data_dir` in `dimos/utils/data.py`. You should probably extract that function and use it: \n  \n ``` \n REGISTRY_DIR = get_user_data_dir() / "runs" \n ```

- **PR #726**:
  > > > > Just missing the rationale on my end, \n > > > Pubsub is already a light adapter layer, expecting just `publish()` and `subscribe()` from implementations which can be in any language, CPP in case of LCM \n > > > What is the expected benefit of bumping an abstraction layer a notch higher to publish() and subscribe() being in rust? Is the idea to gain speed? which computations are you expect...


### Architecture (142 comments)

#### File / module organization (94)

- **PR #702** in `dimos/hardware/manipulators/xarm/xarm_driver.py`:
  > self._disposables already exists on Module.

- **PR #829** in `docs/concepts/modules.md`:
  > ```suggestion \n Some examples of modules are: \n ```

- **PR #1365** in `dimos/core/module_coordinator.py`:
  > continue stopping other modules even if one errors

- **PR #1488** in `dimos/navigation/patrolling/module.py`:
  > I've used Jeff's RPC in multiple places, including this PR, but I don't think it makes sense here. In this case, I want the navigation module to notify me when the goal has been reached (or declared a failure). I can't do that via RPC.

- **PR #713** in `dimos/protocol/service/lcmservice.py`:
  > I think this breaks pickling. Example if you run `dimos-robot run unitree-go2-agentic`: \n  \n ``` \n Pickle encoding error: cannot pickle 'LCM' object                                                                                                                                                                                                                                                      ...

#### Abstraction (25)

- **PR #955** in `dimos/models/vl/base.py`:
  > ```suggestion \n     @abstractmethod \n     def is_set_up(self) -> None: \n ```

- **PR #1280** in `dimos/teleop/phone/phone_teleop_module.py`:
  > If you want to restrict inheritance, you have to use an `ABC`. With them, you get errors if you don't implement the abstract methods.

- **PR #918** in `dimos/hardware/manipulators/piper/piper_wrapper.py`:
  > The `try-except` should wrap just `from piper_sdk import C_PiperInterface_V2` at the start of the function. There's no need to place so much code inside the block.

- **PR #1451** in `dimos/core/tests/demo_devex.py`:
  > Too much MCP duplication. \n  \n You have: \n  \n * wait_for_mcp in dimos/core/tests/e2e_mcp_killtest.py \n * _wait_for_mcp in dimos/core/test_e2e_mcp_stress.py \n * wait_for_mcp in dimos/core/tests/e2e_devex_test.py \n  \n So many other MCP functions are duplicated. \n  \n I already have an mcp client in agents/mcp/mcp_client.py , but in that case "client" refers to the whole Module. \n  \n Like ...

- **PR #720**:
  > There are some mypy errors. (Sorry, I need to turn mypy on in CI.) \n  \n You can get the errors with: \n  \n ```bash \n export MYPYPATH=/opt/ros/jazzy/lib/python3.12/site-packages \n mypy dimos \n ``` \n  \n It shows: \n  \n ``` \n dimos/msgs/nav_msgs/OccupancyGrid.py:22: error: Skipping analyzing "dimos_lcm.nav_msgs": module is installed, but missing library stubs or py.typed marker ...

#### Design patterns (13)

- **PR #970** in `dimos/manipulation/control/dual_trajectory_setter.py`:
  > ```suggestion \n     waypoints: list[list[float]] = field(default_factory=list) \n     generated_trajectory: JointTrajectory | None = None \n ```

- **PR #1357** in `dimos/control/coordinator.py`:
  > I see this pattern a lot, but I don't understand it. If the subscription fails to happen, the entire system is borked, no? There's no point in continuing, so you might as well let the exception happen.

- **PR #1035** in `dimos/simulation/engines/mujoco_engine.py`:
  > I see this pattern a lot in the code where you're copying values only up to a point. \n  \n But I think this just silently ignores errors. Is there a valid reason why write_joint_positions would be sent more positions than can be stored? I think you should let the code throw.

- **PR #1064** in `docs/concepts/README.md`:
  > > The building blocks of DimOS, modules run in parallel \n  \n I'm not sure "building blocks" is a good metaphor, because it implies they're low level. Personally, I'd describe modules as "the unit of deployment in DimOS", but the description in `modules.md` is probably better: "Modules are subsystems on a robot that operate autonomously".  \n  \n > are singleton python classes \n  \n This i...

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Dependencies (6)

- **PR #1229** in `pyproject.toml`:
  > I've removed this dependency.

- **PR #917** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > Rerun is listed as a core dependency. Why the try-except?

- **PR #1234** in `dimos/manipulation/manipulation_module.py`:
  > Please don't use inline imports unless they're to avoid circular imports.

- **PR #868** in `dimos/dashboard/support/html_generation.py`:
  > Just use Jinja2. We already have it installed (although not as a direct dependency). \n  \n HTML and JS should not be defined inline like in this file.

- **PR #1384** in `dimos/utils/cli/lcmspy/lcmspy.py`:
  > `list(deque)` is atomic because it's implemented in C and holds the GIL. It's an implementation detail. Python is already moving towards removing the GIL. When that's mainstream, you'll have Python code adding a value and C code iterating over it to create the list. \n  \n I don't think it's an ideal fix. It only prevents mutations by implication, because the code for `list()` is holding the glo...

#### Separation of concerns (4)

- **PR #583** in `dimos/robot/unitree_webrtc/connectionModule.py`:
  > Is this file used anywhere? Seems to contain a lot of duplicate code from unitree_go2.py like modular/connection_module.py .

- **PR #1536** in `dimos/memory2/codecs/test_codecs.py`:
  > I think all imports in tests should be at the top because there is no speed concern since everything has to be imported anyway.

- **PR #720** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > I agree. In my branch I'm actually adding some OccupancyGrid functions too, but I'm adding them in different files. \n  \n I actually think this about all code in `dimos/msgs/`. \n  \n There are two issues at play here: \n  \n * IMHO, code should not provide transformations which are not exact and depend on a particular strategy. For example, `get_closest_free_point` depends on how you want ...


### Logic / Bugs (139 comments)

#### Logic errors (122)

- **PR #1022** in `README.md`:
  > This is a broken link.

- **PR #900** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > I think this should be cached

- **PR #900** in `rerun_pr_comparison_summary.txt`:
  > I think this should be deleted.

- **PR #1451** in `dimos/core/test_e2e_mcp_stress.py`:
  > There's another `_mcp_call` in `robot/cli/dimos.py` which uses `urllib.request.urlopen`. This one shorter and sweeter. (But I still think all of this MCP stuff should be a class.)

- **PR #1114**:
  > TL;DR: I think we should be able to specify how something is meant to be transported without reifying the transport. \n  \n --- \n  \n I view a topic as the equivalent of a connection string for a database. (Maybe I should use a different name, not topic.) \n  \n ``` \n from sqlalchemy import create_engine \n from sqlalchemy.orm import sessionmaker \n  \n def make_session(conn_url: str):...

#### Edge cases (9)

- **PR #831** in `dimos/manipulation/control/trajectory_controller/spec.py`:
  > What are these empty functions for?

- **PR #1041** in `bin/hooks/filter_commit_message.py`:
  > But what if the co-author is a human? :)

- **PR #1119** in `dimos/grasping/temp_graspgen_testing.py`:
  > What is the purpose of `_default_object_name`? \n  \n `object_name: str` does not allow for `None` so the `else` clause would only take effect if `object_name` is an empty string. \n  \n Would it not be better to raise an error if an empty string is passed rather than silently replace it with "object"?

- **PR #934** in `docs/data.md`:
  > ~~~suggestion \n ```python skip \n from dimos.utils.data import get_data \n from dimos.utils.testing.replay import SensorReplay \n  \n data_dir = get_data("unitree_office_walk") \n replay = SensorReplay(data_dir) \n ~~~ \n  \n You've demonstrated the value of running the code examples and what happens when code examples aren't executed. :D

- **PR #720** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > I agree. In my branch I'm actually adding some OccupancyGrid functions too, but I'm adding them in different files. \n  \n I actually think this about all code in `dimos/msgs/`. \n  \n There are two issues at play here: \n  \n * IMHO, code should not provide transformations which are not exact and depend on a particular strategy. For example, `get_closest_free_point` depends on how you want ...

#### Race conditions (8)

- **PR #1412** in `dimos/web/plugin_openclaw/index.ts`:
  > The ids are supposed to be unique. It technically works if you don't have two concurrent calls, but we should be able to support it.

- **PR #868** in `dimos/dashboard/module.py`:
  > You need to use a lock to prevent the race condition where two threads try to initialize the stream. \n  \n But I don't understand the pid check. How can it ever be true?

- **PR #1536** in `dimos/core/resource.py`:
  > `object` is almost never the right type. You probably want Any. But `DisposableBase` uses: \n  \n ``` \n     def __exit__( \n         self, \n         exctype: Optional[Type[BaseException]], \n         excinst: Optional[BaseException], \n         exctb: Optional[TracebackType], \n     ) -> None: \n ```

- **PR #1451** in `dimos/agents/mcp/mcp_server.py`:
  > You need start/stop. (Technically, start is also called on the first publish but that's a race condition.) \n  \n ```suggestion \n     try: \n         from dimos.core.transport import pLCMTransport \n  \n         transport: pLCMTransport[str] = pLCMTransport("/human_input") \n         transport.start() \n         transport.publish(message) \n         return _jsonrpc_result_text(req_id, f"Message s...

- **PR #713** in `dimos/protocol/service/lcmservice.py`:
  > I think this breaks pickling. Example if you run `dimos-robot run unitree-go2-agentic`: \n  \n ``` \n Pickle encoding error: cannot pickle 'LCM' object                                                                                                                                                                                                                                                      ...


### Testing (127 comments)

#### Missing tests (99)

- **PR #970** in `dimos/control/test_control.py`:
  > Same for the other such tests.

- **PR #894** in `dimos/agents/skills/navigation.py`:
  > Added back to pass the tests.

- **PR #1436** in `dimos/core/test_daemon.py`:
  > Isn't this the same test as above?

- **PR #955** in `dimos/perception/test_temporal_memory_module.py`:
  > Please don't use `locals()`. \n  \n I think you should define each of these as a fixture and to the cleanup in the fixture so it doesn't have to be done in the tests.

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Test quality (27)

- **PR #1436** in `dimos/core/test_e2e_daemon.py`:
  > Should be a fixture to clean up afterwards.

- **PR #1436** in `dimos/core/test_e2e_daemon.py`:
  > Should be a fixture to clean up afterwards.

- **PR #1436** in `dimos/core/test_per_run_logs.py`:
  > Fixture already cleans up. \n  \n ```suggestion \n ```

- **PR #1436** in `dimos/core/test_e2e_daemon.py`:
  > Please remove all stop/remove. They should happen in fixtures so they're executed even if the test fails.

- **PR #649**:
  > > Before merge need to check that this branch passes pytest -m module. This pytest label is not run in CI \n  \n I've just checked now. 5 are failing, but I don't know when they started failing. I have to check: \n  \n ``` \n FAILED dimos/agents/test_agent_message_streams.py::test_agent_message_video_stream - AssertionError: Expected at least 2 responses, got 0 \n FAILED dimos/agents/test_ag...

#### Test naming (1)

- **PR #1451** in `dimos/robot/cli/dimos.py`:
  > While it makes for a prettier CLI interface, this is error prone as you're trying to interpret strings as JSON. \n  \n It would be more reliable to have: \n  \n ``` \n dimos mcp call move --json-args '{"forward": 10, "left", 20}' \n ``` \n  \n It's not much worse than this: \n  \n ``` \n dimos mcp call move --arg forward=10 --arg left=10 \n ``` \n  \n --- \n  \n But if you want it that way, it's b...


### Type Safety (112 comments)

#### Null / None handling (56)

- **PR #651** in `dimos/perception/detection2d/type/imageDetections.py`:
  > `Optional() -> Optional[]` \n  \n Does this actually compile?

- **PR #970** in `dimos/hardware/manipulators/xarm/arm.py`:
  > Module.start returns None. Blueprints won't check DriverStatus.

- **PR #917** in `dimos/mapping/costmapper.py`:
  > ```suggestion \n     def __init__(self, **kwargs: Any) -> None: \n ```

- **PR #1114** in `dimos/protocol/pubsub/impl/lcmpubsub.py`:
  > `# type: ignore[override]` is not nice.  \n  \n PubSub.subscribe has a different declaration: \n  \n ``` \n     @abstractmethod \n     def subscribe( \n         self, topic: TopicT, callback: Callable[[MsgT, TopicT], None] \n     ) -> Callable[[], None]: \n ``` \n  \n Should it be changed there as well?

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Type annotations (53)

- **PR #651** in `dimos/perception/detection2d/type/imageDetections.py`:
  > `Optional() -> Optional[]` \n  \n Does this actually compile?

- **PR #917** in `dimos/mapping/costmapper.py`:
  > ```suggestion \n     def __init__(self, **kwargs: Any) -> None: \n ```

- **PR #955** in `dimos/models/vl/base.py`:
  > ```suggestion \n     @abstractmethod \n     def is_set_up(self) -> None: \n ```

- **PR #1536** in `dimos/core/resource.py`:
  > `object` is almost never the right type. You probably want Any. But `DisposableBase` uses: \n  \n ``` \n     def __exit__( \n         self, \n         exctype: Optional[Type[BaseException]], \n         excinst: Optional[BaseException], \n         exctb: Optional[TracebackType], \n     ) -> None: \n ```

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Type mismatch (3)

- **PR #927** in `dimos/core/transport.py`:
  > ```suggestion \n     def broadcast(self, _: Out[T] | None, msg: T) -> None: \n ```

- **PR #829** in `docs/api/configuration.md`:
  > Should be `**kwargs: Any` not `object`. \n  \n `Any` essentially disables the type checker. `object` is a specific type. Using `kwargs['x'] + 100` is probably a type error since object doesn't do additions, but with `Any` you can do addition because `kwargs['x']` *could* be a number.

- **PR #815** in `dimos/agents2/skills/test_map_eval.py`:
  > Looping in Python is very slow. You can do this directly in Numpy. \n  \n ```suggestion \n     RED = np.array([255, 0, 0], dtype=np.float32) \n     BLUE = np.array([0, 0, 200], dtype=np.float32) \n     color_threshold = 20 \n  \n     # Convert to float32 for distance calculations \n     image_float = image_arr.astype(np.float32) \n  \n     # Calculate distances to target colors using bro...


### Code Style (94 comments)

#### Naming conventions (35)

- **PR #1411** in `dimos/models/vl/create.py`:
  > Renamed.

- **PR #829** in `dimos/core/module.py`:
  > Why rename cls to self?

- **PR #1221** in `dimos/robot/unitree/g1/blueprints/primitive/uintree_g1_primitive_no_nav.py`:
  > typo in file name `uintree`

- **PR #1550** in `dimos/robot/unitree/g1/blueprints/unitree_g1_blueprints.py`:
  > Both this and the other PR contain `unitree_g1_blueprints.py`, a file which we haven't used in a while. They also use `n_dask_workers` which has been renamed to `n_workers` so these are old files.

- **PR #1114**:
  > So this works, but I think there's a certain bit of complexity with mixins and generics which isn't needed. \n  \n # Just some brainstorming ideas \n  \n The way I view it there are 4 things: \n  \n 1. topics \n 2. brokers \n 3. publishers \n 4. subscribers \n  \n Topics should contain every information about what is subscribed/published to and be just static data (do nothing). \n  \n...

#### Unused code / dead code (27)

- **PR #640** in `dimos/robot/drone/camera_module.py`:
  > not used

- **PR #1144** in `dimos/protocol/pubsub/ddspubsub.py`:
  > This is not needed.

- **PR #815** in `dimos/robot/unitree_webrtc/unitree_go2_blueprints.py`:
  > This is imported but not used.

- **PR #1536** in `dimos/memory2/impl/memory.py`:
  > Using `iterate` triggers `_ = obs.data` which is not needed for knowing just the number of observations.

- **PR #702** in `dimos/hardware/manipulators/xarm/components/state_queries.py`:
  > I'm a bit unsure about the architecture here. It seems like XArmDriver is a single class which had it's methods moved into five mixins: MotionControlComponent, StateQueryComponent, SystemControlComponent, KinematicsComponent, GripperControlComponent. \n  \n I don't think they are real components as they are not used independently in other places and the dependencies are described in comments lik...

#### Simplification (16)

- **PR #1035** in `dimos/simulation/engines/mujoco_engine.py`:
  > Why two? Seems like you're releasing and acquiring unnecessary the second time.

- **PR #1064** in `docs/concepts/README.md`:
  > Personally, I think this is needlessly verbose. \n  \n I'd just say "This page explains general concepts. For specific API docs see ...".

- **PR #1411** in `dimos/perception/perceive_loop_skill.py`:
  > Yeah, I thought it was simpler to have it only follow one query (of multiple things), but the agent can stop and change the query if it needs to add more things.

- **PR #684** in `dimos/core/module_coordinator.py`:
  > Could be. There's a lot of code in that `__init__.py` file which should be extracted out. The monkey patching in it is a bit unnecessary. \n  \n I was thinking of refactoring all of that but for now I just wrapped the DimosCluster in `ModuleCoordinator` to keep the scope smaller. But it's definitely something that should be improved.

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Code duplication (12)

- **PR #1436** in `dimos/core/test_e2e_daemon.py`:
  > Duplicate. Should be at the top.

- **PR #1436** in `dimos/core/test_per_run_logs.py`:
  > Should be moved at the top because it's repeated in every test.

- **PR #960** in `dimos/agents/modules/vlm_agent.py`:
  > This is very similar to Agent.__init__, it should be deduplicated somehow.

- **PR #1277** in `dimos/control/coordinator.py`:
  > Rule of three: if you have three duplicate things, it's best to generalize. You can add: \n  \n ``` \n self._disposables = CompositeDisposable() \n ``` \n in `__init__` and do `self._disposables.dispose()` here.

- **PR #640** in `dimos/web/websocket_vis/websocket_vis_module.py`:
  > This is not the best way to do it. Firstly, it duplicates what `set_gps_travel_goal_points` is doing, but the main issue is that if you set the visualized goal only from foxglove, then you can't visualize the gps goal coming from other places (such as from agents). \n  \n The fix I added is in https://github.com/dimensionalOS/dimos/commit/c7f55f74e0244177631d1b1a5d832af3adc0e8d6 \n  \n dimos/r...

#### Formatting / whitespace (4)

- **PR #726** in `README.md`:
  > NITPICK: I see you've fixed trailing whitespace. That's good, but it should be separate PR because it obscures what's changed and can cause merge conflicts.

- **PR #726** in `.editorconfig`:
  > Ruff doesn't fix the non-python files. Also the pre-commit editorconfig checker is quite fast. \n  \n Many people have their editors set to automatically remove trailing whitespace. If we allow it we'll end up with many conflicts from future contributors.

- **PR #902**:
  > > perfect, I assume you sneaked this reformatting on purpose? we are aware of this? \n  \n Yes. :sweat_smile: Both changes are fixes to the same PR so it makes sense to have them in here... (Technically I only noticed that afterwards, and didn't want to crate another PR.)


### Performance (92 comments)

#### Async / concurrency (59)

- **PR #1114** in `dimos/protocol/pubsub/spec.py`:
  > Need a lock

- **PR #543** in `dimos/agents2/test_agent.py`:
  > This is missing `await`.

- **PR #726** in `dimos_rs/uv.lock`:
  > Why is there a uv.lock file here too?

- **PR #1119** in `dimos/agents/skills/grasping.py`:
  > It seems like you're using the event in conjunction with _latest_grasps to pass a value. If that's the case, you can use `queue.Queue`. They're thread safe and you don't need a lock.

- **PR #1357** in `dimos/hardware/drive_trains/unitree_go2/adapter.py`:
  > A lot of this code is quite repetitive and complex because it has to deal with the same situation over and over again. \n  \n The problem is that UnitreeGo2Adapter has `self._client`, has `self._connected`, etc. But these variables don't change independently. \n  \n If UnitreeGo2Adapter were to take a UnitreeGo2Session (containing a client that's already connected) it wouldn't have to deal with th...

#### Memory (16)

- **PR #1041** in `dimos/protocol/pubsub/shmpubsub.py`:
  > Calls to publish are coming from different threads so I don't think you can reuse the same buffer.

- **PR #955** in `dimos/perception/temporal_memory_example.py`:
  > Using `locals()` is bad practice. Set `temporal_memory = None` at the start and check if it's None here.

- **PR #1536** in `dimos/memory2/type/backend.py`:
  > Shouldn't this class be in `memory2/blobstore/`? Maybe `memory2/blobstore/blobstore.py`. It's documented in that dir.

- **PR #959** in `dimos/dashboard/tf_rerun_module.py`:
  > What greptile wrote makes sense, but I'm not sure what the proper fix for this is. \n  \n Maybe the best way would be to add a `get_buffers` method in `MultiTBuffer` which returns a clone, but such a method would require a lock as well and none of the code there uses locks, so it's a big change. But it looks like the only way.

- **PR #1114**:
  > TL;DR: I think we should be able to specify how something is meant to be transported without reifying the transport. \n  \n --- \n  \n I view a topic as the equivalent of a connection string for a database. (Maybe I should use a different name, not topic.) \n  \n ``` \n from sqlalchemy import create_engine \n from sqlalchemy.orm import sessionmaker \n  \n def make_session(conn_url: str):...

#### Unnecessary computation (11)

- **PR #1436** in `dimos/core/test_cli_stop_status.py`:
  > This takes 13 seconds. It should be marked with `@pytest.mark.slow`.

- **PR #1436** in `dimos/core/test_cli_stop_status.py`:
  > This test takes 7 seconds. It should be marked with `@pytest.mark.slow`.

- **PR #694** in `dimos/agents/agent_huggingface_local.py`:
  > Yes. It does it for imports which are only used for typechecking. This can improve startup performance at runtime.

- **PR #1451** in `dimos/core/test_e2e_mcp_stress.py`:
  > I fail to see how these are stress tests. They're supposed to test the limits of the system. \n  \n Also they're not true end-to-end tests because they don't launch the `dimos` command. `e2e_devex_test.py` and `e2e_mcp_killtest.py` are end-to-end, but they're no tests. \n  \n Normally, it's a good idea to run stress tests in an end-to-end manner because it disconnects the test harness from the sys...

- **PR #1114**:
  > So this works, but I think there's a certain bit of complexity with mixins and generics which isn't needed. \n  \n # Just some brainstorming ideas \n  \n The way I view it there are 4 things: \n  \n 1. topics \n 2. brokers \n 3. publishers \n 4. subscribers \n  \n Topics should contain every information about what is subscribed/published to and be just static data (do nothing). \n  \n...

#### Caching (6)

- **PR #900** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > I think this should be cached

- **PR #1154** in `dimos/core/global_config.py`:
  > Since it's no longer frozen, it's probably best to remove `@cached_property` and replace it with `@property`. People will forget to update this list of keys.

- **PR #1154** in `dimos/visualization/rerun/bridge.py`:
  > D'oh. I see that it's cached now. ~~Also, the way `_visual_override_for_entity_path` is used is a bit odd. It's always called right away. I would assume you use a lambda because you want to save it and reuse it, but it's always called as `self._visual_override_for_entity_path(entity_path)(msg)`. Why not eliminate the lambda and use: `self._visual_override_for_entity_path(entity_path, msg)`~~

- **PR #1041** in `dimos/protocol/pubsub/shmpubsub.py`:
  > Initially I was thinking this can be solved by using a thread local cache: https://docs.python.org/3/library/threading.html#thread-local-data \n  \n But it still needs to be invalidated when the shape changes. To do that reliably requires locks, defeating the purpose. Maybe allocate buffers which are large enough for any message? But if we do that, and we're sending images, that requires image s...

- **PR #1174**:
  > When installing I get this: \n  \n ``` \n uv sync --all-extras \n warning: The `extra-build-dependencies` option is experimental and may change without warning. Pass `--preview-features extra-build-dependencies` to disable this warning. \n Resolved 452 packages in 0.95ms \n   × Failed to build `cyclonedds==0.10.5` \n   ├─▶ The build backend returned an error \n   ╰─▶ Call to `setuptools.bu...


### Nits (88 comments)

#### Cosmetic (83)

- **PR #1543** in `dimos/robot/cli/dimos.py`:
  > Nit: `arg_help`

- **PR #620** in `dimos/robot/unitree_webrtc/unitree_b1/connection.py`:
  > NITPICK: These magic numbers should be constants.

- **PR #1119** in `dimos/core/docker_module.py`:
  > Why is this in start()? Shouldn't it be in `__init__`?

- **PR #868** in `dimos/dashboard/support/zellij_tooling.py`:
  > Is `self` supposed to be `logger` here? Also, is this a static class. It's used as one in: \n  \n ``` \n            ZellijManager.init_zellij_session( \n                 self.log, self.session_name, self.terminal_commands, self.zellij_layout \n             ) \n ```

- **PR #713** in `dimos/protocol/service/lcmservice.py`:
  > I think this breaks pickling. Example if you run `dimos-robot run unitree-go2-agentic`: \n  \n ``` \n Pickle encoding error: cannot pickle 'LCM' object                                                                                                                                                                                                                                                      ...

#### Typos (5)

- **PR #1221** in `dimos/robot/unitree/g1/blueprints/primitive/uintree_g1_primitive_no_nav.py`:
  > typo here too

- **PR #1221** in `dimos/robot/unitree/g1/blueprints/primitive/uintree_g1_primitive_no_nav.py`:
  > typo in file name `uintree`

- **PR #1064** in `docs/development/writing_docs/codeblocks.md`:
  > > nix build .#docker \n  \n Is `#` a typo here?


### Documentation (40 comments)

#### Missing docs (32)

- **PR #726** in `pyproject.toml`:
  > Why is this commented out?

- **PR #819** in `dimos/utils/cli/plot.py`:
  > Should this be uncommented?

- **PR #831**:
  > I've skimmed through and left some comments.

- **PR #829** in `docs/concepts/modules.md`:
  > ```suggestion \n Below is an example of a structure for controlling a robot. Black blocks represent modules and colored lines are connections and message types. It's okay if this doesn't make sense now, it will by the end of this document. \n ```

- **PR #702** in `dimos/hardware/manipulators/xarm/components/state_queries.py`:
  > I completely agree with breaking large classes into reusable and interchangeable components, the problem is that mixins are not the best way to achieve that because they are not good at encapsulation and providing interfaces. \n  \n For example, instead of assuming that `self.arm` exists in the `MotionControlComponent` mixin, you can change it to an actual class that accepts `arm` \n  \n  \n ...

#### TODO / FIXME (8)

- **PR #1174**:
  > > Perhaps in all cases where DDS is imported, we just try except as a hacky way to keep it optional. \n  \n :+1:

- **PR #1364** in `dimos/core/blueprints.py`:
  > This looks quite hack-y. What is the issue? I thought I fixed `from __future__ import annotations`. Can you show an example where it fails?

- **PR #792** in `data/.lfs/apartment.tar.gz`:
  > Hm, I'm not sure. There are quite a few things which need to be moved in there and doing it in this PR would make it even bigger than it already is. I'll add this on my todo list.

- **PR #620** in `dimos/robot/unitree_webrtc/unitree_b1/connection.py`:
  > This creates a new thread every time a move is made. I think it would be better to reuse the thread, but that would me creating a custom timer. \n  \n Of course, since we're pressed for time, it should be okay for now. Maybe add a `TODO: FIXME`

- **PR #640** in `dimos/robot/drone/dji_video_stream.py`:
  > The idea behind `while _running: try-except` is that you can resume after temporary errors. \n  \n But I don't think this applies here. If the exception is that you're trying to read from the stdout of a closed process, that will just spam errors at 10Hz. It's never going to recover. \n  \n A better way is to just remove the try-except and let the threads die. Have a separate way of checking i...


### API Design (37 comments)

#### Request / response (20)

- **PR #1365** in `dimos/robot/unitree/g1/blueprints/perceptive/unitree_g1_detection.py`:
  > cannot serialize lambdas, so using functions

- **PR #927** in `dimos/core/transport.py`:
  > Shouldn't this serialize `qos` and `config` as well?

- **PR #1488** in `dimos/navigation/patrolling/module.py`:
  > Because `tf` does not have subscribe. You always have to request it.

- **PR #815** in `dimos/agents2/skills/interpret_map.py`:
  > You would be surprised how imprecise LLM responses can be. For example, even if you tell it to return `{'point': [x, y]}` (btw, that's invalid JSON as single quotes are not allowed) it sometimes might return `{"point": {"x": 123, "y": 123}}`. \n  \n I'd also check if `point["point"]` is a list.

- **PR #713** in `dimos/protocol/service/lcmservice.py`:
  > I think this breaks pickling. Example if you run `dimos-robot run unitree-go2-agentic`: \n  \n ``` \n Pickle encoding error: cannot pickle 'LCM' object                                                                                                                                                                                                                                                      ...

#### Naming / consistency (14)

- **PR #1119** in `dimos/core/docker_module.py`:
  > `--restart` isn't added here, it's added in `_add_resource_args`.

- **PR #1280** in `dimos/teleop/phone/phone_teleop_module.py`:
  > If you want to restrict inheritance, you have to use an `ABC`. With them, you get errors if you don't implement the abstract methods.

- **PR #1143** in `dimos/core/blueprints.py`:
  > Maybe this should be called `_connect_streams()` and `connection` renamed to `stream` everywhere in this func to match the rest of the renames.

- **PR #1038** in `dimos/protocol/pubsub/benchmark/test_benchmark.py`:
  > I'm not sure if this is a realistic way to benchmark. By generating the message at the start of the loop, it's only measuring how long it takes to transport the message. That's fair, if we're only interested in measuring that aspect of message passing. \n  \n  But real messages also take time to encode, and encodings can be cached giving unrealistic real-world expectations. \n  \n I've tried m...

- **PR #1114**:
  > So this works, but I think there's a certain bit of complexity with mixins and generics which isn't needed. \n  \n # Just some brainstorming ideas \n  \n The way I view it there are 4 things: \n  \n 1. topics \n 2. brokers \n 3. publishers \n 4. subscribers \n  \n Topics should contain every information about what is subscribed/published to and be just static data (do nothing). \n  \n...

#### Backwards compatibility (3)

- **PR #1149** in `docker/navigation/build.sh`:
  > Is https://github.com/dimensionalOS/ros-navigation-autonomy-stack deprecated now? \n  \n Why are we moving it outside `dimensionalOS/`?

- **PR #720** in `dimos/agents2/skills/interpret_map.py`:
  > query_single_frame is an agents1 function which is deprecated. The replacement is `QwenVlModel` used in agents2. You can parse the response with `extract_json_from_llm_response`. (I see `parse_qwen_points_response` is already defined in `dimos/skills/manipulation/pick_and_place.py`) \n  \n I think the query aspect can be abstracted a bit like it's done in `dimos/navigation/visual/query.py` or `d...

- **PR #1172** in `pull_request_template.md`:
  > I think most of this information should be on the issue, not the PR. \n  \n * "Effort Estimate" is only needed if we take it into account when planning. I wouldn't think it's useful to have the estimate after the work was done. \n * "Stack / Category" is more useful on issues. \n  \n Personally I'd say: \n  \n ``` \n ## Problem \n What feature are you adding, or what is broken, missing, or sub-opt...


### Error Handling (27 comments)

#### Missing error handling (27)

- **PR #955** in `dimos/perception/test_temporal_memory_module.py`:
  > Please remove try-except.

- **PR #917** in `dimos/msgs/nav_msgs/OccupancyGrid.py`:
  > Rerun is listed as a core dependency. Why the try-except?

- **PR #900** in `dimos/dashboard/rerun_init.py`:
  > Why convert an exception to a warning? Do we really want to continue if rerun failed?

- **PR #1536** in `dimos/core/resource.py`:
  > `object` is almost never the right type. You probably want Any. But `DisposableBase` uses: \n  \n ``` \n     def __exit__( \n         self, \n         exctype: Optional[Type[BaseException]], \n         excinst: Optional[BaseException], \n         exctb: Optional[TracebackType], \n     ) -> None: \n ```

- **PR #713** in `dimos/protocol/service/lcmservice.py`:
  > I think this breaks pickling. Example if you run `dimos-robot run unitree-go2-agentic`: \n  \n ``` \n Pickle encoding error: cannot pickle 'LCM' object                                                                                                                                                                                                                                                      ...


### Security (12 comments)

#### Input validation (7)

- **PR #1536** in `dimos/memory2/blobstore/sqlite.py`:
  > Dropping unescaped strings into SQL is bad.

- **PR #1536** in `dimos/memory2/blobstore/file.py`:
  > Could be useful to sanitize `stream` to check it doesn't contain `/` or some other bad characters. \n  \n In the other class, stream names must work as tables, so maybe check for alphanumeric + underscore

- **PR #1536** in `dimos/memory2/blobstore/test_blobstore.py`:
  > I think this should be: \n  \n ```suggestion \n @pytest.fixture(params=["file_store", "sqlite_store"]) \n def blob_store(request: pytest.FixtureRequest) -> BlobStore: \n     return request.getfixturevalue(request.param) \n ``` \n  \n Otherwise, you're requesting both fixtures but only using one.

- **PR #1041** in `dimos/protocol/pubsub/shmpubsub.py`:
  > Initially I was thinking this can be solved by using a thread local cache: https://docs.python.org/3/library/threading.html#thread-local-data \n  \n But it still needs to be invalidated when the shape changes. To do that reliably requires locks, defeating the purpose. Maybe allocate buffers which are large enough for any message? But if we do that, and we're sending images, that requires image s...

- **PR #1080**:
  > Personally, I don't like the API. It's similar to what we do with `LCM()` and others where we don't encode the lifecycle into the API. The API is simple, but doesn't give you enough control. \n  \n ## Sessions \n  \n ```python \n store = SqliteStore("recordings/lidar") \n store.save(data) \n ``` \n  \n Without a session, API calls race to create `self._conn`. You could add a lock. But it ...

#### Permissions / auth (3)

- **PR #1041** in `bin/hooks/filter_commit_message.py`:
  > But what if the co-author is a human? :)

- **PR #917** in `dimos/core/global_config.py`:
  > Use Literal, to avoid comments, do proper type checking, and have typer generate help examples. This is how `planner_strategy` does it: \n <img width="935" height="39" alt="2025-12-31_15-13" src="https://github.com/user-attachments/assets/76870e0d-e6d2-455c-936f-ef9fc828bcd3" /> \n  \n --- \n  \n ```python \n ViewerBackend: TypeAlias = Literal["rerun-web", "rerun-native", "foxglove"] \n ......

- **PR #1412** in `dimos/web/plugin_openclaw/index.ts`:
  > This only works if you run both openclaw and dimos on the same machine, right? \n  \n Currently, the MCP server has no auth, but we should probably add auth so we can connect to it from a remote server. Otherwise we will have to run openclaw and dimos on the same machine. \n  \n I think most people run openclaw on AWS or on a local minipc. People probably can't run dimos there. \n  \n (Personally,...

#### Secrets / credentials (2)

- **PR #970** in `dimos/hardware/manipulators/xarm/blueprints.py`:
  > We probably don't want hardcoded ips here.

- **PR #1114**:
  > TL;DR: I think we should be able to specify how something is meant to be transported without reifying the transport. \n  \n --- \n  \n I view a topic as the equivalent of a connection string for a database. (Maybe I should use a different name, not topic.) \n  \n ``` \n from sqlalchemy import create_engine \n from sqlalchemy.orm import sessionmaker \n  \n def make_session(conn_url: str):...


### Imports (5 comments)

#### Unused imports (3)

- **PR #1112**:
  > > why are we doing this \n  \n @spomichter Many of the ruff checks are disabled. I've fixed the ones with very few issues. The biggest change is F401 which auto removes unused imports.

- **PR #900** in `dimos/dashboard/__init__.py`:
  > I don't like the idea of imports having side effects. (Ruff removes unused imports like this (but this disabled until I fix all the errors).) It would be better to make `_init_rerun` a public function and it should be called to initialize rerun.

- **PR #918** in `dimos/hardware/manipulators/piper/piper_wrapper.py`:
  > We have this problem different connection types in Unitree Go2 as well. But instead of handling both situations in each function by using an `if`, we handle each type in its own class. \n  \n ``` \n     def start(self):  \n         match self.connection_type: \n             case "webrtc": \n                 self.connection = UnitreeWebRTCConnection(**self.connection_config) \n             c...

#### Import organization (2)

- **PR #1112**:
  > > why are we doing this \n  \n @spomichter Many of the ruff checks are disabled. I've fixed the ones with very few issues. The biggest change is F401 which auto removes unused imports.

- **PR #900** in `dimos/dashboard/__init__.py`:
  > I don't like the idea of imports having side effects. (Ruff removes unused imports like this (but this disabled until I fix all the errors).) It would be better to make `_init_rerun` a public function and it should be called to initialize rerun.


### Uncategorized (415 comments)

Comments that didn't match any pattern category:

- **PR #539**: I created https://github.com/dimensionalOS/dimos/issues/545

- **PR #539**: Yeah, this won't last much. I'm guessing the next steps will be a to use a realistic office environment, so these particular assets will be deleted. I'll look at get_data later.

- **PR #557**: SortedList already has .bisect_left . There's no need to create a new list.

- **PR #557**: You also don't need to create a timestamps list. \n  \n And to delete you can use `del self._items[:keep_idx]`.

- **PR #566**: The MuJoCo camera is an ideal pinhole camera with no distortion, so I guess you can just configure it to skip rectification.

- **PR #577**: This was separately merged into https://github.com/dimensionalOS/dimos/pull/570

- **PR #570**: Yes, this is my commit from the Foxglove stuff. Exploration can be triggered from Foxglove so I removed it.

- **PR #570**: "command-center-extension" is the Foxglove extension I wrote. This gitignore is needed to un-ignore package.json.

- **PR #570**: @leshy About the merging of the two branches. Basically since this adds Twist and the foxglove extension adds the keyboard teleop which needs twist. To do it separately, Alex would have to have a Twist PR, I would have a Foxglove PR without Twist and then a separate PR to use Twist in Foxglove once ...

- **PR #543**: These threads are never cleaned up. I think you should use a ThreadPoolExecutor on SkillContainer to manage executing on different threads.

---

## Paul's Review Style Summary

Based on analysis of all comments, Paul's review style characteristics:

- **Socratic approach**: 22% of comments are questions — Paul often asks 'why' rather than dictating
- **Occasionally provides code**: 7% include code suggestions
- **Gives positive feedback**: 6% include praise or approval
- **Moderate length**: Median comment is 103 chars — thorough but not verbose
