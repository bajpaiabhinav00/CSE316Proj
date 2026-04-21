from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from process import Process
from system_simulation import CycleSnapshot, System, create_sample_processes


class SimulationDashboard(tk.Tk):
    """Desktop UI for the adaptive resource allocation simulation."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Adaptive Resource Allocation Simulator")
        self.geometry("1380x860")
        self.minsize(1180, 760)
        self.configure(bg="#0b1020")

        self.system = self._create_system()
        self.max_cycles = 10
        self.refresh_delay_ms = 700
        self.is_running = False
        self.history_limit = 30
        self.cpu_history: list[float] = []
        self.memory_history: list[float] = []
        self.completed_processes = 0

        self._configure_style()
        self._build_layout()
        self._render_initial_state()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("App.TFrame", background="#0b1020")
        style.configure("Panel.TFrame", background="#121a30", relief="flat")
        style.configure("PanelHeader.TLabel", background="#121a30", foreground="#dbe6ff", font=("Avenir Next", 15, "bold"))
        style.configure("Body.TLabel", background="#121a30", foreground="#aebcde", font=("Avenir Next", 11))
        style.configure("MetricValue.TLabel", background="#121a30", foreground="#f8fbff", font=("Avenir Next", 26, "bold"))
        style.configure("MetricCaption.TLabel", background="#121a30", foreground="#8ea3d4", font=("Avenir Next", 10))
        style.configure("Accent.TButton", font=("Avenir Next", 11, "bold"), padding=10)
        style.map(
            "Accent.TButton",
            background=[("active", "#2647c8"), ("!disabled", "#1c36a5")],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure("Secondary.TButton", font=("Avenir Next", 10), padding=8)
        style.configure(
            "Treeview",
            background="#11182c",
            fieldbackground="#11182c",
            foreground="#edf2ff",
            rowheight=28,
            borderwidth=0,
            font=("Avenir Next", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#1a2441",
            foreground="#dce5ff",
            font=("Avenir Next", 10, "bold"),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#2446c1")])

    def _build_layout(self) -> None:
        container = ttk.Frame(self, style="App.TFrame", padding=18)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container, style="App.TFrame")
        header.pack(fill="x", pady=(0, 14))

        title = tk.Label(
            header,
            text="Adaptive Resource Allocation Simulator",
            bg="#0b1020",
            fg="#f8fbff",
            font=("Avenir Next", 24, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Priority-based CPU scheduling and memory-aware swapping in a multiprogramming system",
            bg="#0b1020",
            fg="#90a6d8",
            font=("Avenir Next", 12),
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(container, style="Panel.TFrame", padding=16)
        controls.pack(fill="x", pady=(0, 14))

        ttk.Label(controls, text="Controls", style="PanelHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.start_button = ttk.Button(controls, text="Start", style="Accent.TButton", command=self.start_simulation)
        self.start_button.grid(row=0, column=1, padx=(16, 8), sticky="e")
        ttk.Button(controls, text="Step", style="Secondary.TButton", command=self.step_simulation).grid(
            row=0, column=2, padx=8
        )
        ttk.Button(controls, text="Reset", style="Secondary.TButton", command=self.reset_simulation).grid(
            row=0, column=3, padx=(8, 0)
        )
        controls.columnconfigure(0, weight=1)

        slider_row = ttk.Frame(controls, style="Panel.TFrame")
        slider_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        slider_row.columnconfigure(1, weight=1)

        ttk.Label(slider_row, text="Speed", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.speed_scale = tk.Scale(
            slider_row,
            from_=200,
            to=1400,
            resolution=100,
            orient="horizontal",
            bg="#121a30",
            fg="#dbe6ff",
            troughcolor="#24345f",
            highlightthickness=0,
            activebackground="#3f67ff",
            command=self._update_speed,
        )
        self.speed_scale.set(self.refresh_delay_ms)
        self.speed_scale.grid(row=0, column=1, sticky="ew")

        metrics = ttk.Frame(container, style="App.TFrame")
        metrics.pack(fill="x", pady=(0, 14))

        self.cpu_card = self._build_metric_card(metrics, "CPU Usage", "Tracks simulated processor pressure", 0)
        self.memory_card = self._build_metric_card(metrics, "Memory Usage", "Tracks total resident memory load", 1)
        self.cycle_card = self._build_metric_card(metrics, "Cycle", "Current simulation iteration", 2)
        self.running_card = self._build_metric_card(metrics, "Running PID", "Process currently assigned to CPU", 3)

        body = ttk.Frame(container, style="App.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=3)
        body.rowconfigure(1, weight=2)

        left_top = ttk.Frame(body, style="Panel.TFrame", padding=16)
        left_top.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        ttk.Label(left_top, text="Active Processes", style="PanelHeader.TLabel").pack(anchor="w")
        ttk.Label(left_top, text="Live view of process burst time, priority, memory, and state", style="Body.TLabel").pack(
            anchor="w", pady=(4, 12)
        )

        columns = ("pid", "burst", "priority", "memory", "state")
        self.process_table = ttk.Treeview(left_top, columns=columns, show="headings", height=12)
        for name, label, width in (
            ("pid", "PID", 80),
            ("burst", "Burst Time", 110),
            ("priority", "Priority", 100),
            ("memory", "Memory (MB)", 120),
            ("state", "State", 120),
        ):
            self.process_table.heading(name, text=label)
            self.process_table.column(name, width=width, anchor="center")
        self.process_table.pack(fill="both", expand=True)

        left_bottom = ttk.Frame(body, style="Panel.TFrame", padding=16)
        left_bottom.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(left_bottom, text="Adaptive Actions Log", style="PanelHeader.TLabel").pack(anchor="w")
        ttk.Label(left_bottom, text="Policy decisions taken when system load crosses thresholds", style="Body.TLabel").pack(
            anchor="w", pady=(4, 12)
        )
        self.log_text = tk.Text(
            left_bottom,
            height=10,
            bg="#11182c",
            fg="#edf2ff",
            insertbackground="#edf2ff",
            relief="flat",
            wrap="word",
            font=("Avenir Next", 10),
            padx=12,
            pady=12,
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        right_top = ttk.Frame(body, style="Panel.TFrame", padding=16)
        right_top.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        ttk.Label(right_top, text="Scheduling Queue", style="PanelHeader.TLabel").pack(anchor="w")
        ttk.Label(right_top, text="Dynamic order after priority updates and swaps", style="Body.TLabel").pack(
            anchor="w", pady=(4, 12)
        )
        self.schedule_list = tk.Listbox(
            right_top,
            bg="#11182c",
            fg="#edf2ff",
            selectbackground="#3056df",
            relief="flat",
            font=("Avenir Next", 11),
            activestyle="none",
            highlightthickness=0,
        )
        self.schedule_list.pack(fill="both", expand=True)

        right_bottom = ttk.Frame(body, style="Panel.TFrame", padding=16)
        right_bottom.grid(row=1, column=1, sticky="nsew")
        ttk.Label(right_bottom, text="Resource History", style="PanelHeader.TLabel").pack(anchor="w")
        ttk.Label(right_bottom, text="Recent CPU and memory trends across cycles", style="Body.TLabel").pack(
            anchor="w", pady=(4, 12)
        )
        self.history_canvas = tk.Canvas(
            right_bottom,
            bg="#11182c",
            highlightthickness=0,
            height=240,
        )
        self.history_canvas.pack(fill="both", expand=True)

        footer = tk.Label(
            container,
            text="Tip: Start for autoplay, Step for manual analysis, Reset to restore the initial workload.",
            bg="#0b1020",
            fg="#7f95c6",
            font=("Avenir Next", 10),
        )
        footer.pack(anchor="w", pady=(12, 0))

    def _build_metric_card(self, parent: ttk.Frame, title: str, caption: str, column: int) -> dict[str, tk.Label]:
        card = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 10) if column < 3 else 0)
        parent.columnconfigure(column, weight=1)

        ttk.Label(card, text=title, style="PanelHeader.TLabel").pack(anchor="w")
        value = tk.Label(card, text="--", bg="#121a30", fg="#f8fbff", font=("Avenir Next", 26, "bold"))
        value.pack(anchor="w", pady=(12, 6))
        ttk.Label(card, text=caption, style="MetricCaption.TLabel").pack(anchor="w")
        return {"frame": card, "value": value}

    def _create_system(self) -> System:
        return System(create_sample_processes())

    def _render_initial_state(self) -> None:
        initial_snapshot = CycleSnapshot(
            cycle_number=0,
            cpu_usage=self.system.monitor.measure_cpu_usage(self.system.process_manager),
            memory_usage=self.system.monitor.measure_memory_usage(self.system.process_manager),
            running_process_pid=None,
            adaptive_actions=["Simulation ready"],
            active_processes=list(self.system.process_manager.get_active_processes()),
            scheduling_order=list(self.system.scheduler.get_schedule(self.system.process_manager)),
            swapped_processes=list(self.system.process_manager.swapped_processes),
        )
        self._apply_snapshot(initial_snapshot, append_history=False)

    def _update_speed(self, value: str) -> None:
        self.refresh_delay_ms = int(float(value))

    def start_simulation(self) -> None:
        if self.is_running:
            self.is_running = False
            self.start_button.configure(text="Resume")
            return

        self.is_running = True
        self.start_button.configure(text="Pause")
        self._run_automatic_cycle()

    def _run_automatic_cycle(self) -> None:
        if not self.is_running:
            return
        if not self.system.has_work() or self.system.cycle_number >= self.max_cycles:
            self.is_running = False
            self.start_button.configure(text="Start")
            return

        self.step_simulation()
        if self.is_running:
            self.after(self.refresh_delay_ms, self._run_automatic_cycle)

    def step_simulation(self) -> None:
        if not self.system.has_work() or self.system.cycle_number >= self.max_cycles:
            self.is_running = False
            self.start_button.configure(text="Start")
            return

        before_count = len(self.system.process_manager.get_active_processes())
        snapshot = self.system.run_cycle_snapshot()
        after_count = len(snapshot.active_processes)
        self.completed_processes += max(0, before_count - after_count)
        self._apply_snapshot(snapshot, append_history=True)

    def reset_simulation(self) -> None:
        self.is_running = False
        self.start_button.configure(text="Start")
        self.system = self._create_system()
        self.cpu_history.clear()
        self.memory_history.clear()
        self.completed_processes = 0
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._render_initial_state()

    def _apply_snapshot(self, snapshot: CycleSnapshot, append_history: bool) -> None:
        if append_history:
            self.cpu_history.append(snapshot.cpu_usage)
            self.memory_history.append(snapshot.memory_usage)
            self.cpu_history = self.cpu_history[-self.history_limit :]
            self.memory_history = self.memory_history[-self.history_limit :]

        self.cpu_card["value"].configure(text=f"{snapshot.cpu_usage:.1f}%")
        self.memory_card["value"].configure(text=f"{snapshot.memory_usage:.1f}%")
        self.cycle_card["value"].configure(text=str(snapshot.cycle_number))
        running_label = f"PID {snapshot.running_process_pid}" if snapshot.running_process_pid is not None else "Idle"
        self.running_card["value"].configure(text=running_label)

        self._color_metric_card(self.cpu_card["frame"], snapshot.cpu_usage, primary="#40c4ff", warning="#ffb020", danger="#ff5d73")
        self._color_metric_card(
            self.memory_card["frame"], snapshot.memory_usage, primary="#5dd39e", warning="#ffb020", danger="#ff5d73"
        )

        self.process_table.delete(*self.process_table.get_children())
        for process in snapshot.active_processes:
            self.process_table.insert(
                "",
                "end",
                values=(process.pid, process.burst_time, process.priority, process.memory, process.state),
            )

        self.schedule_list.delete(0, "end")
        if snapshot.scheduling_order:
            for position, process in enumerate(snapshot.scheduling_order, start=1):
                label = f"{position}. PID {process.pid} | Priority {process.priority} | Burst {process.burst_time}"
                self.schedule_list.insert("end", label)
        else:
            self.schedule_list.insert("end", "No active processes in the queue")

        self.log_text.configure(state="normal")
        if append_history:
            message = f"Cycle {snapshot.cycle_number}: " + " | ".join(snapshot.adaptive_actions) + "\n"
            self.log_text.insert("1.0", message)
        else:
            self.log_text.insert("1.0", "Ready to simulate adaptive scheduling.\n")
        self.log_text.configure(state="disabled")

        self._draw_history(snapshot)

    def _color_metric_card(self, frame: ttk.Frame, value: float, primary: str, warning: str, danger: str) -> None:
        color = primary
        if value >= 80:
            color = danger
        elif value >= 60:
            color = warning
        frame.configure(style="Panel.TFrame")
        for child in frame.winfo_children():
            if isinstance(child, tk.Label):
                if child.cget("font") == ("Avenir Next", 26, "bold"):
                    child.configure(fg=color)

    def _draw_history(self, snapshot: CycleSnapshot) -> None:
        canvas = self.history_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 320)
        height = max(canvas.winfo_height(), 220)
        left = 44
        top = 18
        right = width - 18
        bottom = height - 32

        canvas.create_rectangle(left, top, right, bottom, outline="#263455")
        for level in range(0, 101, 25):
            y = bottom - ((bottom - top) * level / 100)
            canvas.create_line(left, y, right, y, fill="#1c2744", dash=(2, 4))
            canvas.create_text(left - 10, y, text=str(level), fill="#8ea3d4", font=("Avenir Next", 9))

        cpu_points = self._history_points(self.cpu_history, left, top, right, bottom)
        memory_points = self._history_points(self.memory_history, left, top, right, bottom)

        if len(cpu_points) >= 4:
            canvas.create_line(*cpu_points, fill="#40c4ff", width=3, smooth=True)
        if len(memory_points) >= 4:
            canvas.create_line(*memory_points, fill="#5dd39e", width=3, smooth=True)

        if self.cpu_history:
            canvas.create_text(right - 70, top + 12, text="CPU", fill="#40c4ff", font=("Avenir Next", 10, "bold"))
        if self.memory_history:
            canvas.create_text(right - 20, top + 12, text="MEM", fill="#5dd39e", font=("Avenir Next", 10, "bold"))

        canvas.create_text(
            left,
            bottom + 18,
            anchor="w",
            text=f"Swapped: {len(snapshot.swapped_processes)}   Completed: {self.completed_processes}",
            fill="#8ea3d4",
            font=("Avenir Next", 10),
        )

    def _history_points(self, history: list[float], left: int, top: int, right: int, bottom: int) -> list[float]:
        if not history:
            return []
        if len(history) == 1:
            x = (left + right) / 2
            y = bottom - ((bottom - top) * history[0] / 100)
            return [x, y, x + 1, y]

        step = (right - left) / max(1, len(history) - 1)
        points: list[float] = []
        for index, value in enumerate(history):
            x = left + (index * step)
            y = bottom - ((bottom - top) * value / 100)
            points.extend((x, y))
        return points


def main() -> None:
    app = SimulationDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
