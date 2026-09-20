#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import Point, Pose
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose
from rclpy.node import Node


class GoalCommander(Node):
    def __init__(self) -> None:
        super().__init__("goal_commander")

        self.declare_parameter("goal_topic", "/drone/goal")
        self.declare_parameter("world_name", "default")
        self.declare_parameter("entity_name", "clover")
        self.declare_parameter("spawn_x", -5.0)
        self.declare_parameter("spawn_y", 3.4)
        self.declare_parameter("spawn_z", 1.0)
        self.declare_parameter("goal_tolerance", 0.35)
        self.declare_parameter("max_speed", 1.2)
        self.declare_parameter("control_rate_hz", 20.0)

        goal_topic = self.get_parameter("goal_topic").value
        self.world_name = self.get_parameter("world_name").value
        self.entity_name = self.get_parameter("entity_name").value

        self.goal_tolerance = float(self.get_parameter("goal_tolerance").value)
        self.max_speed = float(self.get_parameter("max_speed").value)

        control_rate_hz = float(self.get_parameter("control_rate_hz").value)
        self.control_period = 1.0 / max(1.0, control_rate_hz)

        self.create_subscription(Point, goal_topic, self.goal_callback, 10)
        self.pose_client = self.create_client(
            SetEntityPose,
            f"/world/{self.world_name}/set_pose",
        )

        self.control_timer = self.create_timer(self.control_period, self.control_loop)

        self.active_goal = None
        self.goal_active = False
        self.pending_future = None
        self.current_pose = Pose()
        self.current_pose.position.x = float(self.get_parameter("spawn_x").value)
        self.current_pose.position.y = float(self.get_parameter("spawn_y").value)
        self.current_pose.position.z = float(self.get_parameter("spawn_z").value)
        self.current_pose.orientation.w = 1.0

        self.get_logger().info("Goal commander is ready.")
        self.get_logger().info(f"Send goals to {goal_topic} as geometry_msgs/msg/Point.")

    def goal_callback(self, msg: Point) -> None:
        self.active_goal = Point(x=msg.x, y=msg.y, z=msg.z)
        self.goal_active = True
        self.get_logger().info(
            f"Received goal: x={msg.x:.2f}, y={msg.y:.2f}, z={msg.z:.2f}"
        )

    def _publish_goal_pose(self, pose: Pose) -> None:
        if not self.pose_client.service_is_ready():
            if not self.pose_client.wait_for_service(timeout_sec=0.1):
                self.get_logger().warn("Waiting for Gazebo SetEntityPose service...")
                return

        request = SetEntityPose.Request()
        request.entity = Entity(name=self.entity_name, type=Entity.MODEL)
        request.pose = pose
        self.pending_future = self.pose_client.call_async(request)

    def control_loop(self) -> None:
        if self.pending_future is not None:
            if not self.pending_future.done():
                return

            response = self.pending_future.result()
            self.pending_future = None
            if response is None or not response.success:
                self.get_logger().warn("Gazebo rejected the pose update.")
                return

            self.current_pose = self._target_pose

        if not self.goal_active or self.active_goal is None:
            return

        dx = self.active_goal.x - self.current_pose.position.x
        dy = self.active_goal.y - self.current_pose.position.y
        dz = self.active_goal.z - self.current_pose.position.z

        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        if distance < self.goal_tolerance:
            self.goal_active = False
            self.get_logger().info("Goal reached.")
            return

        step = min(self.max_speed * self.control_period, distance)
        if distance > 1e-6:
            scale = step / distance
        else:
            scale = 0.0

        self._target_pose = Pose()
        self._target_pose.position.x = self.current_pose.position.x + dx * scale
        self._target_pose.position.y = self.current_pose.position.y + dy * scale
        self._target_pose.position.z = self.current_pose.position.z + dz * scale
        self._target_pose.orientation = self.current_pose.orientation

        self._publish_goal_pose(self._target_pose)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GoalCommander()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
