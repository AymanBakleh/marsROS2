#!/usr/bin/env python3

import threading
import tkinter as tk
from tkinter import ttk

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node


class MissionGuiNode(Node):
    def __init__(self) -> None:
        super().__init__("mission_gui")

        self.drone_pub = self.create_publisher(Point, "/drone/goal", 10)
        self.tetrix_pub = self.create_publisher(Point, "/tetrix/goal", 10)

        self.root = tk.Tk()
        self.root.title("Mission Goal Publisher")
        self.root.geometry("360x300")

        self._build_layout()

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Drone goal (x, y, z)").grid(row=0, column=0, columnspan=2, sticky="w")
        self.drone_x = tk.StringVar(value="0.0")
        self.drone_y = tk.StringVar(value="0.0")
        self.drone_z = tk.StringVar(value="1.0")

        ttk.Label(frame, text="x").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.drone_x).grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text="y").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.drone_y).grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="z").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.drone_z).grid(row=3, column=1, sticky="ew")

        ttk.Button(frame, text="Send Drone Goal", command=self.send_drone_goal).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(6, 12)
        )

        ttk.Label(frame, text="Tetrix goal (x, y)").grid(row=5, column=0, columnspan=2, sticky="w")
        self.tetrix_x = tk.StringVar(value="0.0")
        self.tetrix_y = tk.StringVar(value="0.0")

        ttk.Label(frame, text="x").grid(row=6, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.tetrix_x).grid(row=6, column=1, sticky="ew")
        ttk.Label(frame, text="y").grid(row=7, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.tetrix_y).grid(row=7, column=1, sticky="ew")

        ttk.Button(frame, text="Send Tetrix Goal", command=self.send_tetrix_goal).grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(6, 12)
        )

        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_text).grid(row=9, column=0, columnspan=2, sticky="w")

        frame.columnconfigure(1, weight=1)

    def _parse_float(self, value: str) -> float:
        return float(value.strip())

    def send_drone_goal(self) -> None:
        try:
            x = self._parse_float(self.drone_x.get())
            y = self._parse_float(self.drone_y.get())
            z = self._parse_float(self.drone_z.get())
        except ValueError:
            self.status_text.set("Invalid drone value")
            return

        msg = Point(x=x, y=y, z=z)
        self.drone_pub.publish(msg)
        self.status_text.set(f"Drone goal sent: ({x:.2f}, {y:.2f}, {z:.2f})")

    def send_tetrix_goal(self) -> None:
        try:
            x = self._parse_float(self.tetrix_x.get())
            y = self._parse_float(self.tetrix_y.get())
        except ValueError:
            self.status_text.set("Invalid Tetrix value")
            return

        msg = Point(x=x, y=y, z=0.0)
        self.tetrix_pub.publish(msg)
        self.status_text.set(f"Tetrix goal sent: ({x:.2f}, {y:.2f})")

    def run(self) -> None:
        self.root.mainloop()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MissionGuiNode()

    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
