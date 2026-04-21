# Adaptive Resource Allocation in Multiprogramming Systems

This project simulates how an operating system can adapt CPU scheduling and memory usage in a multiprogramming environment. It is a Python-based simulation, not a real kernel implementation.

## Classes and Modules

- `Process` in `process.py`
  - Represents a process with `pid`, `burst_time`, `priority`, and `memory`.
  - Supports one-cycle execution, priority changes, and formatted state output.

- `ProcessManager` in `process_manager.py`
  - Stores active and swapped processes.
  - Calculates total memory usage and swaps out the lowest-priority process when needed.

- `MonitoringModule` in `monitoring.py`
  - Simulates current CPU and memory usage from the active process set.

- `AdaptiveDecisionEngine` in `adaptive_engine.py`
  - Applies adaptive policies:
    - If CPU usage is above 80%, lower priority of heavy processes.
    - If memory usage is above 75%, swap out the lowest-priority process.
    - If CPU usage is below 50%, raise priority of waiting processes.

- `Scheduler` in `scheduler.py`
  - Produces a priority-based scheduling order.
  - Runs the highest-priority process for one cycle.

- `System` in `system_simulation.py`
  - Coordinates monitoring, adaptive decisions, scheduling, and formatted reporting for each cycle.

## How to Run

```bash
python3 system_simulation.py
```

For the desktop UI:

```bash
python3 simulation_ui.py
```

For the browser UI on localhost:

```bash
python3 web_simulation.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Notes

- Uses only built-in Python modules.
- Includes a small time delay between cycles for a real-time feel.
- Runs multiple cycles and prints CPU usage, memory usage, process state, and scheduling order.
- Includes a local `tkinter` dashboard with live metrics, scheduling queue, adaptive action log, and resource history.
- Includes a localhost web dashboard with the same simulation logic, designed for browser-based interaction.
