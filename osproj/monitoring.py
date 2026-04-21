from __future__ import annotations

from process_manager import ProcessManager


class MonitoringModule:
    """Calculates simulated CPU and memory usage for the current cycle."""

    def __init__(self, cpu_capacity: int, memory_capacity: int) -> None:
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity

    def measure_cpu_usage(self, process_manager: ProcessManager) -> float:
        active_processes = process_manager.get_active_processes()
        if not active_processes:
            return 0.0

        total_burst = sum(process.burst_time for process in active_processes)
        pressure = len(active_processes) * 10
        cpu_usage = (total_burst + pressure) / self.cpu_capacity * 100
        return min(cpu_usage, 100.0)

    def measure_memory_usage(self, process_manager: ProcessManager) -> float:
        return min((process_manager.total_memory_usage() / self.memory_capacity) * 100, 100.0)
