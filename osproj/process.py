from dataclasses import dataclass, field


@dataclass(order=False)
class Process:
    """Represents a simulated process in the multiprogramming system."""

    pid: int
    burst_time: int
    priority: int
    memory: int
    state: str = field(default="ready")

    def run_for_cycle(self) -> None:
        """Execute the process for one simulation cycle."""
        if self.burst_time > 0:
            self.burst_time -= 1
            self.state = "running" if self.burst_time > 0 else "completed"

    def adjust_priority(self, delta: int, minimum: int = 1, maximum: int = 10) -> None:
        """Adjust priority while keeping it within a valid range."""
        updated = self.priority + delta
        self.priority = max(minimum, min(maximum, updated))

    def is_complete(self) -> bool:
        return self.burst_time <= 0

    def describe(self) -> str:
        return (
            f"PID={self.pid:<2} "
            f"burst={self.burst_time:<2} "
            f"priority={self.priority:<2} "
            f"memory={self.memory:<3}MB "
            f"state={self.state}"
        )
