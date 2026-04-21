from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable, List

from adaptive_engine import AdaptiveDecisionEngine
from monitoring import MonitoringModule
from process import Process
from process_manager import ProcessManager
from scheduler import Scheduler


@dataclass
class CycleSnapshot:
    """Structured system state for CLI and UI rendering."""

    cycle_number: int
    cpu_usage: float
    memory_usage: float
    running_process_pid: int | None
    adaptive_actions: List[str]
    active_processes: List[Process]
    scheduling_order: List[Process]
    swapped_processes: List[Process]


class System:
    """Coordinates monitoring, adaptation, and scheduling for each cycle."""

    def __init__(
        self,
        processes: Iterable[Process],
        cpu_capacity: int = 125,
        memory_capacity: int = 1000,
    ) -> None:
        self.process_manager = ProcessManager(processes)
        self.monitor = MonitoringModule(cpu_capacity=cpu_capacity, memory_capacity=memory_capacity)
        self.decision_engine = AdaptiveDecisionEngine()
        self.scheduler = Scheduler()
        self.cycle_number = 0

    def run_cycle_snapshot(self) -> CycleSnapshot:
        self.cycle_number += 1

        cpu_usage = self.monitor.measure_cpu_usage(self.process_manager)
        memory_usage = self.monitor.measure_memory_usage(self.process_manager)
        actions = self.decision_engine.evaluate(cpu_usage, memory_usage, self.process_manager)

        # Re-measure after adaptation because priorities or memory residency may have changed.
        cpu_usage = self.monitor.measure_cpu_usage(self.process_manager)
        memory_usage = self.monitor.measure_memory_usage(self.process_manager)

        running_process = self.scheduler.run_next_process(self.process_manager)
        self.process_manager.remove_completed()
        schedule = self.scheduler.get_schedule(self.process_manager)

        return CycleSnapshot(
            cycle_number=self.cycle_number,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            running_process_pid=running_process.pid if running_process else None,
            adaptive_actions=actions,
            active_processes=list(self.process_manager.get_active_processes()),
            scheduling_order=list(schedule),
            swapped_processes=list(self.process_manager.swapped_processes),
        )

    def run_cycle(self) -> str:
        snapshot = self.run_cycle_snapshot()
        return self._format_state(snapshot)

    def has_work(self) -> bool:
        return bool(self.process_manager.get_active_processes())

    def _format_state(self, snapshot: CycleSnapshot) -> str:
        process_lines = [process.describe() for process in snapshot.active_processes] or ["No active processes"]
        schedule_order = (
            " -> ".join(f"PID {process.pid}(P{process.priority})" for process in snapshot.scheduling_order) or "Empty"
        )
        swapped = ", ".join(f"PID {process.pid}" for process in snapshot.swapped_processes) or "None"
        running_label = f"PID {snapshot.running_process_pid}" if snapshot.running_process_pid is not None else "None"

        lines = [
            f"Cycle {snapshot.cycle_number}",
            f"CPU Usage: {snapshot.cpu_usage:.2f}%",
            f"Memory Usage: {snapshot.memory_usage:.2f}%",
            f"Running Process: {running_label}",
            f"Adaptive Actions: {'; '.join(snapshot.adaptive_actions)}",
            "Active Processes:",
            *[f"  {line}" for line in process_lines],
            f"Scheduling Order: {schedule_order}",
            f"Swapped Processes: {swapped}",
        ]
        return "\n".join(lines)


def create_sample_processes() -> List[Process]:
    return [
        Process(pid=1, burst_time=9, priority=5, memory=180),
        Process(pid=2, burst_time=6, priority=3, memory=120),
        Process(pid=3, burst_time=8, priority=4, memory=200),
        Process(pid=4, burst_time=5, priority=2, memory=150),
        Process(pid=5, burst_time=7, priority=1, memory=160),
        Process(pid=6, burst_time=4, priority=6, memory=140),
        Process(pid=7, burst_time=3, priority=2, memory=90),
    ]


def run_simulation(cycles: int = 10, delay_seconds: float = 0.5) -> None:
    system = System(create_sample_processes())

    for _ in range(cycles):
        if not system.has_work():
            break
        print(system.run_cycle())
        print("-" * 72)
        if delay_seconds > 0:
            time.sleep(delay_seconds)


if __name__ == "__main__":
    run_simulation()
