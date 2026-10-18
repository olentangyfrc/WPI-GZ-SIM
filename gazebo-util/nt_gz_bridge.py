#!/usr/bin/env python3
"""
Zero-Latency Direct Memory Gazebo Swerve Bridge
Bypasses subprocess and CLI execution by publishing directly into
Gazebo's native transport IPC layer.
"""

import time
import sys

try:
    import ntcore
except ImportError:
    print("[Error] 'pyntcore' is not installed.", file=sys.stderr)
    sys.exit(1)

# Dynamically import gz or ignition transport
try:
    from gz.transport14 import Node
    from gz.msgs11.double_pb2 import Double
    GZ_VERSION = "Jetty (gz-sim 10 / transport14)"
except ImportError:
    try:
        from gz.transport13 import Node
        from gz.msgs10.double_pb2 import Double
        GZ_VERSION = "Harmonic (gz-sim 8 / transport13)"
    except ImportError:
        try:
            from gz.transport import Node
            from gz.msgs.double_pb2 import Double
            GZ_VERSION = "Gazebo Generic"
        except ImportError:
            print("[Error] Native gz-transport bindings could not be loaded.", file=sys.stderr)
            sys.exit(1)


def main():
    print(f"=== Native Low-Latency Swerve Bridge [{GZ_VERSION}] ===")

    # 1. Connect to WPILib Sim
    nt_inst = ntcore.NetworkTableInstance.getDefault()
    nt_inst.startClient4("GzDirectBridge")
    nt_inst.setServer("127.0.0.1", ntcore.NetworkTableInstance.kDefaultPort4)

    table = nt_inst.getTable("Swerve")
    steer_sub = table.getDoubleArrayTopic("SteerAngles").subscribe([0.0, 0.0, 0.0, 0.0])

    # 2. Direct In-Memory Gazebo Node
    node = Node()
    topics = [
        "/model/frc_swerve/joint/fl_steer_joint/cmd_pos",
        "/model/frc_swerve/joint/fr_steer_joint/cmd_pos",
        "/model/frc_swerve/joint/bl_steer_joint/cmd_pos",
        "/model/frc_swerve/joint/br_steer_joint/cmd_pos",
    ]

    pubs = [node.advertise(t, Double) for t in topics]
    msgs = [Double() for _ in range(4)]

    print("[Bridge] Direct C++ shared-memory publisher active.")
    print("[Bridge] Forwarding at 50 Hz. Press Ctrl+C to stop.\n")

    try:
        while True:
            angles = steer_sub.get()
            if len(angles) >= 4:
                for i in range(4):
                    msgs[i].data = float(angles[i])
                    pubs[i].publish(msgs[i])

            # 20ms update rate matching WPILib robot loop exactly
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped.")


if __name__ == "__main__":
    main()