import os

import asyncio
from bleak import BleakClient

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

from std_msgs.msg import String


class SwitchBotController(Node):
    def __init__(self, mac_list):
        super().__init__('switchbot_controller')
        self.subscription = self.create_subscription(String, 'command', self.command_callback, 10)

        self.bot_mac_list = mac_list
        self.bot_write_char = "cba20002-224d-11e6-9fb8-0002a5d5c51b"
        self.turn_on = bytearray([0x57, 0x01, 0x01])
        self.turn_off = bytearray([0x57, 0x01, 0x02])

    async def execute_command(self, action):
        success = False
        attempts = 0
        while attempts < 10 and not success:
            attempts += 1
            for bot_mac in self.bot_mac_list:
                try:
                    self.get_logger().info(f'Connecting to Bot at {bot_mac}...')
                    async with BleakClient(bot_mac) as client:
                        self.get_logger().info("Connected.")
                        if action == 'on':
                            await client.write_gatt_char(self.bot_write_char, self.turn_on)
                            self.get_logger().info('Turning ON')
                        elif action == 'off':
                            await client.write_gatt_char(self.bot_write_char, self.turn_off)
                            self.get_logger().info('Turning OFF')
                        success = True
                        break
                except Exception as e:
                    self.get_logger().info(f'Failed to execute command: {str(e)}')

    def command_callback(self, msg):
        if msg.data in ['on', 'off']:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.execute_command(msg.data))
            except RuntimeError:
                self.get_logger().warn("No running event loop, creating a new one")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.execute_command(msg.data))



def main(args=None):
    rclpy.init(args=args)
    mac_list = [os.getenv('SWITCHBOT_MAC', 'CE:2A:46:46:22:76')]

    SBC = SwitchBotController(mac_list)
    executor = MultiThreadedExecutor()
    executor.add_node(SBC)

    try:
        executor.spin()
    finally:
        SBC.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
