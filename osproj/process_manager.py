from __future__ import annotations

from typing import Iterable, List

from process import Process


class ProcessManager:
    """Maintains active and swapped processes."""

    def __init__(self, processes: Iterable[Process]) -> None:
        self.active_processes: List[Process] = list(processes)
        self.swapped_processes: List[Process] = []

    def get_active_processes(self) -> List[Process]:
        return [process for process in self.active_processes if not process.is_complete()]

    def get_waiting_processes(self) -> List[Process]:
        return [process for process in self.get_active_processes() if process.state != "running"]

    def total_memory_usage(self) -> int:
        return sum(process.memory for process in self.get_active_processes())

    def remove_completed(self) -> None:
        self.active_processes = [p for p in self.active_processes if not p.is_complete()]

    def swap_out_lowest_priority(self) -> Process | None:
        candidates = self.get_active_processes()
        if not candidates:
            return None

        process_to_swap = min(candidates, key=lambda process: (process.priority, -process.memory, process.pid))
        process_to_swap.state = "swapped"
        self.active_processes.remove(process_to_swap)
        self.swapped_processes.append(process_to_swap)
        return process_to_swap
