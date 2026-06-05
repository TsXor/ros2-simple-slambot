import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import cast

import rcl_interfaces.msg
import rclpy
from geometry_msgs.msg import Twist, TwistStamped


class TeleopTwistKeyboardGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Teleop Twist Keyboard - GUI")
        self.root.resizable(False, False)

        # ROS2 初始化
        rclpy.init()
        self.node = rclpy.create_node('teleop_twist_keyboard_gui')

        # 参数（与原程序一致）
        read_only_descriptor = rcl_interfaces.msg.ParameterDescriptor(read_only=True)
        self.stamped = cast(bool, self.node.declare_parameter('stamped', False, read_only_descriptor).value)
        self.frame_id = cast(str, self.node.declare_parameter('frame_id', '', read_only_descriptor).value)
        self.speed = cast(float, self.node.declare_parameter('speed', 0.5, read_only_descriptor).value)
        self.turn = cast(float, self.node.declare_parameter('turn', 1.0, read_only_descriptor).value)

        if not self.stamped and self.frame_id:
            raise Exception("'frame_id' can only be set when 'stamped' is True")

        if self.stamped:
            pub = self.node.create_publisher(TwistStamped, 'cmd_vel', 10)
            def publish_twist(twist: Twist):
                twist_msg = TwistStamped()
                twist_msg.header.stamp = self.node.get_clock().now().to_msg()
                twist_msg.header.frame_id = self.frame_id
                twist_msg.twist = twist
                pub.publish(twist_msg)
        else:
            pub = self.node.create_publisher(Twist, 'cmd_vel', 10)
            def publish_twist(twist: Twist):
                pub.publish(twist)

        self.publish_twist = publish_twist

        # 状态变量
        self.lock = threading.Lock()
        self.active_keys = set[str]()
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.holonomic = False
        self.running = True

        # 控制绑定（与原程序完全一致）
        self.move_bindings = {
            'i': (1, 0, 0, 0),
            'o': (1, 0, 0, -1),
            'j': (0, 0, 0, 1),
            'l': (0, 0, 0, -1),
            'u': (1, 0, 0, 1),
            ',': (-1, 0, 0, 0),
            '.': (-1, 0, 0, 1),
            'm': (-1, 0, 0, -1),
            'O': (1, -1, 0, 0),
            'I': (1, 0, 0, 0),
            'J': (0, 1, 0, 0),
            'L': (0, -1, 0, 0),
            'U': (1, 1, 0, 0),
            '<': (-1, 0, 0, 0),
            '>': (-1, -1, 0, 0),
            'M': (-1, 1, 0, 0),
            't': (0, 0, 1, 0),
            'b': (0, 0, -1, 0),
        }
        self.special_keysym_map = {
            'comma': ',',
            'period': '.',
            'less': '<',
            'greater': '>',
        }

        self.speed_bindings = {
            'q': (1.1, 1.1),
            'z': (0.9, 0.9),
            'w': (1.1, 1.0),
            'x': (0.9, 1.0),
            'e': (1.0, 1.1),
            'c': (1.0, 0.9),
        }

        # 小写键到 Holonomic 大写键的映射
        self.holo_map = {
            'u': 'U', 'i': 'I', 'o': 'O',
            'j': 'J', 'l': 'L',
            'm': 'M', ',': '<', '.': '>',
        }

        self.debounce_timeout = 40
        self.debounce_id = dict[str, str]()

        self.setup_ui()
        self.setup_keyboard()

        # 启动 ROS2 后台线程
        self.spin_thread = threading.Thread(target=rclpy.spin, args=(self.node,))
        self.spin_thread.start()
        self.pub_thread = threading.Thread(target=self.publish_loop)
        self.pub_thread.start()

    def setup_ui(self):
        """构建 tkinter 界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0)

        # 标题
        title = ttk.Label(
            main_frame,
            text="Teleop Twist Keyboard",
            font=('Arial', 14, 'bold')
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # ========== 方向控制按钮 ==========
        dir_frame = ttk.LabelFrame(
            main_frame,
            text="Movement (Click & Hold)",
            padding="5"
        )
        dir_frame.grid(
            row=1, column=0, columnspan=3,
            pady=5, sticky='we'
        )
        for i in range(3):
            dir_frame.columnconfigure(i, weight=1)

        dir_buttons = [
            ('u', 'U\n(↖)', 0, 0),
            ('i', 'I\n(↑)', 0, 1),
            ('o', 'O\n(↗)', 0, 2),
            ('j', 'J\n(←)', 1, 0),
            ('k', 'K\n(■)', 1, 1),
            ('l', 'L\n(→)', 1, 2),
            ('m', 'M\n(↙)', 2, 0),
            (',', '<\n(↓)', 2, 1),
            ('.', '>\n(↘)', 2, 2),
        ]

        self.dir_buttons = {}
        for key, label, r, c in dir_buttons:
            btn = tk.Button(
                dir_frame,
                text=label,
                width=8,
                height=2,
                font=('Arial', 10)
            )
            btn.grid(row=r, column=c, padx=3, pady=3, sticky='we')
            on_press, on_release = self.make_button_cb(key)
            btn.bind('<ButtonPress-1>', on_press)
            btn.bind('<ButtonRelease-1>', on_release)
            self.dir_buttons[key] = btn

        # ========== 垂直控制按钮 ==========
        vert_frame = ttk.LabelFrame(
            main_frame,
            text="Vertical",
            padding="5"
        )
        vert_frame.grid(
            row=2, column=0, columnspan=3,
            pady=5, sticky='we'
        )

        for key, label in [('t', 'T\n(Up)'), ('b', 'B\n(Down)')]:
            btn = tk.Button(
                vert_frame,
                text=label,
                width=10,
                height=2,
                font=('Arial', 10)
            )
            btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
            on_press, on_release = self.make_button_cb(key)
            btn.bind('<ButtonPress-1>', on_press)
            btn.bind('<ButtonRelease-1>', on_release)

        # ========== 速度控制按钮 ==========
        speed_frame = ttk.LabelFrame(
            main_frame,
            text="Speed Control",
            padding="5"
        )
        speed_frame.grid(
            row=3, column=0, columnspan=3,
            pady=5, sticky='we'
        )

        speed_buttons = [
            ('q', 'Q\n+All'), ('z', 'Z\n-All'),
            ('w', 'W\n+Lin'), ('x', 'X\n-Lin'),
            ('e', 'E\n+Ang'), ('c', 'C\n-Ang'),
        ]

        for i, (key, label) in enumerate(speed_buttons):
            btn = tk.Button(
                speed_frame,
                text=label,
                width=8,
                height=2,
                font=('Arial', 9)
            )
            btn.grid(row=0, column=i, padx=2, pady=2)
            btn.bind('<ButtonPress-1>',
                     lambda e, k=key: self.on_speed_button(k))

        # ========== Holonomic 模式切换 ==========
        self.holo_var = tk.BooleanVar(value=False)
        holo_cb = ttk.Checkbutton(
            main_frame,
            text="Holonomic Mode (Shift)",
            variable=self.holo_var,
            command=self.on_holo_toggle
        )
        holo_cb.grid(row=4, column=0, columnspan=3, pady=5)

        # ========== 速度显示 ==========
        self.speed_label = ttk.Label(
            main_frame,
            text=self.get_speed_text(),
            font=('Courier', 11)
        )
        self.speed_label.grid(row=5, column=0, columnspan=3, pady=5)

        # ========== 状态显示 ==========
        self.status_label = ttk.Label(
            main_frame,
            text="Status: Ready",
            font=('Courier', 10)
        )
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # ========== 帮助文本 ==========
        help_frame = ttk.LabelFrame(main_frame, text="Help", padding="5")
        help_frame.grid(
            row=7, column=0, columnspan=3,
            pady=5, sticky='we'
        )

        help_text = (
            "Keyboard: Press keys when window is focused\n"
            "Buttons: Click and hold to move\n"
            "Shift: Hold Shift for holonomic mode (or check box)\n"
            "Close window to quit"
        )
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT)
        help_label.pack()

    def setup_keyboard(self):
        """绑定键盘事件到主窗口"""
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_holo_toggle(self):
        """Holonomic 复选框切换回调"""
        self.holonomic = self.holo_var.get()
        with self.lock:
            self.update_twist()

    def make_button_cb(self, key: str):
        if key == 'k':
            def on_press(e):
                self.active_keys.clear()
                self.update_twist()
            def on_release(e):
                pass
        else:
            def on_press(e):
                self.active_keys.add(key)
                self.update_twist()
            def on_release(e):
                self.active_keys.discard(key)
                self.update_twist()
        return on_press, on_release

    def on_speed_button(self, key: str):
        """速度按钮点击：调整速度参数"""
        with self.lock:
            if key in self.speed_bindings:
                s_mult, t_mult = self.speed_bindings[key]
                self.speed *= s_mult
                self.turn *= t_mult
                self.speed_label.config(text=self.get_speed_text())

    def on_key_press(self, event: tk.Event):
        """键盘按下事件"""
        key = event.char

        # 检测 Shift 键进入 Holonomic 模式
        if event.keysym in ('Shift_L', 'Shift_R'):
            self.holo_var.set(True)
            self.holonomic = True
            return

        if not key: return

        with self.lock:
            if key in self.speed_bindings: # 速度调整键
                s_mult, t_mult = self.speed_bindings[key]
                self.speed *= s_mult
                self.turn *= t_mult
                self.speed_label.config(text=self.get_speed_text())
            elif key == '\x03': # Ctrl-C
                self.on_close()
                return
            elif key == 'k': # 停止键
                self.active_keys.clear()
                self.update_twist()
            elif key in self.move_bindings: # 方向键
                debounce_id = self.debounce_id.pop(key, None)
                if debounce_id is None:
                    self.active_keys.add(key)
                    self.update_twist()
                else:
                    self.root.after_cancel(debounce_id)
            else: # 其他任意键
                # 停止（与原程序一致）
                self.active_keys.clear()
                self.update_twist()

    def on_key_release(self, event: tk.Event):
        """键盘释放事件"""
        if event.keysym in self.special_keysym_map:
            key = self.special_keysym_map[event.keysym]
        else:
            key = event.keysym

        # 检测 Shift 键退出 Holonomic 模式
        if event.keysym in ('Shift_L', 'Shift_R'):
            self.holo_var.set(False)
            self.holonomic = False
            return

        if not key: return

        with self.lock:
            if key in self.move_bindings:
                def actually_discard():
                    with self.lock:
                        del self.debounce_id[key]
                        self.active_keys.discard(key)
                        self.update_twist()
                debounce_id = self.root.after(self.debounce_timeout, actually_discard)
                self.debounce_id[key] = debounce_id

    def update_twist(self):
        """根据当前激活的键和 Holonomic 状态计算 Twist 分量"""
        x, y, z, th = 0.0, 0.0, 0.0, 0.0

        for key in self.active_keys:
            effective_key = key
            # 若处于 Holonomic 模式且为小写方向键，映射到对应大写键
            if self.holonomic and key in self.holo_map:
                effective_key = self.holo_map[key]

            if effective_key in self.move_bindings:
                mx, my, mz, mth = self.move_bindings[effective_key]
                x += mx
                y += my
                z += mz
                th += mth

        self.x = x
        self.y = y
        self.z = z
        self.th = th

        # 更新状态标签
        keys_str = ', '.join(sorted(self.active_keys)) if self.active_keys else 'None'
        self.status_label.config(
            text=f"Active: {keys_str} | x:{x:.1f} y:{y:.1f} z:{z:.1f} th:{th:.1f}"
        )

    def get_speed_text(self):
        """返回当前速度文本（与原程序 vels 函数对应）"""
        return f"currently:  speed {self.speed:.2f}  turn {self.turn:.2f}"

    def publish_loop(self):
        """后台发布线程：以 10Hz 持续发布 Twist 消息"""
        period = 0.1  # 10 Hz

        while self.running and rclpy.ok():
            start_time = time.time()

            with self.lock:
                x, y, z, th = self.x, self.y, self.z, self.th
                speed, turn = self.speed, self.turn

            twist = Twist()
            twist.linear.x = x * speed
            twist.linear.y = y * speed
            twist.linear.z = z * speed
            twist.angular.x = 0.0
            twist.angular.y = 0.0
            twist.angular.z = th * turn
            self.publish_twist(twist)

            elapsed = time.time() - start_time
            if elapsed < period:
                time.sleep(period - elapsed)

    def on_close(self):
        """关闭窗口：发送停止消息并清理资源"""
        self.running = False

        # 发送零速消息（与原程序 finally 块一致）
        twist = Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0
        self.publish_twist(twist)

        rclpy.shutdown()
        self.root.destroy()

    def run(self):
        """启动 tkinter 主循环"""
        self.root.mainloop()
        self.spin_thread.join(timeout=1.0)
        self.pub_thread.join(timeout=1.0)


def main():
    gui = TeleopTwistKeyboardGUI()
    gui.run()

if __name__ == '__main__':
    main()
