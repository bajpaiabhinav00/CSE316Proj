from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from system_simulation import CycleSnapshot, System, create_sample_processes


ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "web_static"


class SimulationController:
    """Keeps mutable simulation state for the local web UI."""

    def __init__(self) -> None:
        self.max_cycles = 60
        self.reset()

    def reset(self) -> dict[str, Any]:
        self.system = System(create_sample_processes())
        self.completed_processes = 0
        self.cpu_history: list[float] = []
        self.memory_history: list[float] = []
        snapshot = CycleSnapshot(
            cycle_number=0,
            cpu_usage=self.system.monitor.measure_cpu_usage(self.system.process_manager),
            memory_usage=self.system.monitor.measure_memory_usage(self.system.process_manager),
            running_process_pid=None,
            adaptive_actions=["Simulation ready"],
            active_processes=list(self.system.process_manager.get_active_processes()),
            scheduling_order=list(self.system.scheduler.get_schedule(self.system.process_manager)),
            swapped_processes=list(self.system.process_manager.swapped_processes),
        )
        return self.serialize(snapshot)

    def step(self) -> dict[str, Any]:
        if not self.system.has_work() or self.system.cycle_number >= self.max_cycles:
            return self.status()

        before_count = len(self.system.process_manager.get_active_processes())
        snapshot = self.system.run_cycle_snapshot()
        after_count = len(snapshot.active_processes)
        self.completed_processes += max(0, before_count - after_count)
        self.cpu_history.append(snapshot.cpu_usage)
        self.memory_history.append(snapshot.memory_usage)
        self.cpu_history = self.cpu_history[-30:]
        self.memory_history = self.memory_history[-30:]
        return self.serialize(snapshot)

    def status(self) -> dict[str, Any]:
        snapshot = CycleSnapshot(
            cycle_number=self.system.cycle_number,
            cpu_usage=self.system.monitor.measure_cpu_usage(self.system.process_manager),
            memory_usage=self.system.monitor.measure_memory_usage(self.system.process_manager),
            running_process_pid=None,
            adaptive_actions=["Awaiting next action"],
            active_processes=list(self.system.process_manager.get_active_processes()),
            scheduling_order=list(self.system.scheduler.get_schedule(self.system.process_manager)),
            swapped_processes=list(self.system.process_manager.swapped_processes),
        )
        return self.serialize(snapshot)

    def serialize(self, snapshot: CycleSnapshot) -> dict[str, Any]:
        return {
            "cycleNumber": snapshot.cycle_number,
            "cpuUsage": round(snapshot.cpu_usage, 2),
            "memoryUsage": round(snapshot.memory_usage, 2),
            "runningProcessPid": snapshot.running_process_pid,
            "adaptiveActions": list(snapshot.adaptive_actions),
            "activeProcesses": [
                {
                    "pid": process.pid,
                    "burstTime": process.burst_time,
                    "priority": process.priority,
                    "memory": process.memory,
                    "state": process.state,
                }
                for process in snapshot.active_processes
            ],
            "schedulingOrder": [
                {
                    "pid": process.pid,
                    "burstTime": process.burst_time,
                    "priority": process.priority,
                    "memory": process.memory,
                    "state": process.state,
                }
                for process in snapshot.scheduling_order
            ],
            "swappedProcesses": [
                {
                    "pid": process.pid,
                    "burstTime": process.burst_time,
                    "priority": process.priority,
                    "memory": process.memory,
                    "state": process.state,
                }
                for process in snapshot.swapped_processes
            ],
            "cpuHistory": list(self.cpu_history),
            "memoryHistory": list(self.memory_history),
            "completedProcesses": self.completed_processes,
            "hasWork": self.system.has_work(),
            "maxCycles": self.max_cycles,
        }


CONTROLLER = SimulationController()


class SimulationHandler(BaseHTTPRequestHandler):
    """Serves the local dashboard and JSON endpoints."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._send_json(CONTROLLER.status())
            return

        if parsed.path == "/" or parsed.path == "/index.html":
            self._serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/styles.css":
            self._serve_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
            return

        if parsed.path == "/app.js":
            self._serve_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reset":
            self._send_json(CONTROLLER.reset())
            return

        if parsed.path == "/api/step":
            self._send_json(CONTROLLER.step())
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Missing asset")
            return

        content = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SimulationHandler)
    print("Serving Adaptive Resource Allocation dashboard on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
