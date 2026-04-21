from __future__ import annotations

from typing import List

from process_manager import ProcessManager


class AdaptiveDecisionEngine:
    """Applies adaptive policies based on system load."""

    def evaluate(self, cpu_usage: float, memory_usage: float, process_manager: ProcessManager) -> List[str]:
        actions: List[str] = []
        active_processes = process_manager.get_active_processes()

        if cpu_usage > 80:
            heavy_processes = sorted(
                active_processes,
                key=lambda process: (process.burst_time, process.memory),
                reverse=True,
            )[:2]
            for process in heavy_processes:
                previous_priority = process.priority
                process.adjust_priority(-1)
                if process.priority != previous_priority:
                    actions.append(
                        f"Reduced priority of PID {process.pid} from {previous_priority} to {process.priority}"
                    )

        if memory_usage > 75:
            swapped = process_manager.swap_out_lowest_priority()
            if swapped is not None:
                actions.append(
                    f"Swapped out PID {swapped.pid} to reduce memory pressure"
                )

        if cpu_usage < 40:
            for process in process_manager.get_waiting_processes():
                previous_priority = process.priority
                process.adjust_priority(1)
                if process.priority != previous_priority:
                    actions.append(
                        f"Increased priority of waiting PID {process.pid} from {previous_priority} to {process.priority}"
                    )

        if not actions:
            actions.append("No adaptive changes required")

        return actions
