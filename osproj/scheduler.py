from __future__ import annotations

from typing import List

from process import Process
from process_manager import ProcessManager


class Scheduler:
    """Creates a dynamic priority-based scheduling order."""

    def get_schedule(self, process_manager: ProcessManager) -> List[Process]:
        active_processes = process_manager.get_active_processes()
        return sorted(
            active_processes,
            key=lambda process: (-process.priority, process.burst_time, process.pid),
        )

    def run_next_process(self, process_manager: ProcessManager) -> Process | None:
        schedule = self.get_schedule(process_manager)
        if not schedule:
            return None

        for process in process_manager.get_active_processes():
            if process.state != "swapped":
                process.state = "ready"

        next_process = schedule[0]
        next_process.run_for_cycle()
        return next_process
