#!/usr/bin/env python3

import math
from enum import Enum
from typing import List, Optional, Tuple

import rclpy
from geometry_msgs.msg import Point, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import String


class MissionState(Enum):
    PATROL = "patrol"
    FIRE_RESPONSE = "fire_response"
    FIRE_HOLD = "fire_hold"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


class PatrolManager(Node):
    def __init__(self) -> None:
        super().__init__("patrol_manager")

        self.loop_hz = float(self.declare_parameter("loop_hz", 10.0).value)
        self.goal_tolerance = float(self.declare_parameter("goal_tolerance", 0.25).value)
        self.max_speed_xy = float(self.declare_parameter("max_speed_xy", 0.5).value)
        self.max_speed_yaw = float(self.declare_parameter("max_speed_yaw", 1.2).value)
        self.k_xy = float(self.declare_parameter("k_xy", 0.9).value)
        self.k_yaw = float(self.declare_parameter("k_yaw", 1.6).value)
        self.fire_hold_seconds = float(self.declare_parameter("fire_hold_seconds", 2.0).value)

        raw_flat = self.declare_parameter(
            "waypoints_flat",
            [0.0, 0.0, 2.0, 2.0, 2.0, -2.0, -2.0, -2.0, -2.0, 2.0],
        ).value
        flat = [float(v) for v in raw_flat]
        if len(flat) % 2 != 0:
            raise RuntimeError("Parameter 'waypoints_flat' must have an even number of entries")
        self.waypoints: List[Tuple[float, float]] = [
            (flat[i], flat[i + 1]) for i in range(0, len(flat), 2)
        ]
        if not self.waypoints:
            raise RuntimeError("Parameter 'waypoints' cannot be empty")

        self.state = MissionState.PATROL
        self.patrol_index = 0
        self.fire_target: Optional[Tuple[float, float]] = None
        self.fire_arrival_time: Optional[float] = None

        self.robot_x: Optional[float] = None
        self.robot_y: Optional[float] = None
        self.robot_yaw: Optional[float] = None

        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.status_pub = self.create_publisher(String, "/mission/status", 10)

        self.create_subscription(Odometry, "/odom", self.odom_callback, 20)
        self.create_subscription(Point, "/fire_target", self.fire_target_callback, 10)

        self.timer = self.create_timer(1.0 / self.loop_hz, self.control_loop)
        self.publish_status("Mission started: patrol")

    def odom_callback(self, msg: Odometry) -> None:
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.robot_yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)

    def fire_target_callback(self, msg: Point) -> None:
        self.fire_target = (float(msg.x), float(msg.y))
        self.state = MissionState.FIRE_RESPONSE
        self.fire_arrival_time = None
        self.publish_status(
            f"Fire target received: ({self.fire_target[0]:.2f}, {self.fire_target[1]:.2f})"
        )

    def publish_status(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)
        self.get_logger().info(text)

    def nearest_patrol_index(self, x: float, y: float) -> int:
        best_idx = 0
        best_dist = float("inf")
        for idx, (wx, wy) in enumerate(self.waypoints):
            d = math.hypot(wx - x, wy - y)
            if d < best_dist:
                best_dist = d
                best_idx = idx
        return best_idx

    def target_for_state(self) -> Tuple[float, float]:
        if self.state in (MissionState.FIRE_RESPONSE, MissionState.FIRE_HOLD) and self.fire_target:
            return self.fire_target
        return self.waypoints[self.patrol_index]

    def control_loop(self) -> None:
        if self.robot_x is None or self.robot_y is None or self.robot_yaw is None:
            return

        tx, ty = self.target_for_state()
        ex_world = tx - self.robot_x
        ey_world = ty - self.robot_y
        dist = math.hypot(ex_world, ey_world)

        # For holonomic drive, command velocity in base frame toward target.
        c = math.cos(self.robot_yaw)
        s = math.sin(self.robot_yaw)
        ex_base = c * ex_world + s * ey_world
        ey_base = -s * ex_world + c * ey_world

        desired_heading = math.atan2(ey_world, ex_world)
        heading_err = math.atan2(
            math.sin(desired_heading - self.robot_yaw),
            math.cos(desired_heading - self.robot_yaw),
        )

        cmd = Twist()
        cmd.linear.x = clamp(self.k_xy * ex_base, -self.max_speed_xy, self.max_speed_xy)
        cmd.linear.y = clamp(self.k_xy * ey_base, -self.max_speed_xy, self.max_speed_xy)
        cmd.angular.z = clamp(self.k_yaw * heading_err, -self.max_speed_yaw, self.max_speed_yaw)

        if dist <= self.goal_tolerance:
            if self.state == MissionState.PATROL:
                self.patrol_index = (self.patrol_index + 1) % len(self.waypoints)
                self.publish_status(
                    f"Patrol waypoint reached, next index: {self.patrol_index}"
                )
            elif self.state == MissionState.FIRE_RESPONSE:
                self.state = MissionState.FIRE_HOLD
                self.fire_arrival_time = self.get_clock().now().nanoseconds / 1e9
                self.publish_status("Reached fire target, extinguishing...")
            elif self.state == MissionState.FIRE_HOLD and self.fire_arrival_time is not None:
                now_sec = self.get_clock().now().nanoseconds / 1e9
                if now_sec - self.fire_arrival_time >= self.fire_hold_seconds:
                    self.publish_status("Fire extinguished, resuming patrol")
                    self.state = MissionState.PATROL
                    self.fire_target = None
                    self.fire_arrival_time = None
                    self.patrol_index = self.nearest_patrol_index(self.robot_x, self.robot_y)

            # Stop briefly at goal.
            cmd = Twist()

        self.cmd_pub.publish(cmd)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PatrolManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
