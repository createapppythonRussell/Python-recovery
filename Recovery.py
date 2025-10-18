from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from plyer import battery
from kivy.core.window import Window

Window.clearcolor = (0, 0, 0, 1)


# ---------- Классическое Recovery ----------
class ClassicRecovery(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.menu_items = [
            "Reboot system now",
            "Apply update from ADB",
            "Wipe data/factory reset",
            "Wipe cache partition",
            "Power off"
        ]
        self.selected = 0

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.title = Label(
            text='-- Android Recovery --',
            font_size='24sp',
            color=(1, 0.8, 0, 1),
            size_hint=(1, 0.15)
        )
        self.layout.add_widget(self.title)

        # Меню
        self.labels = []
        for item in self.menu_items:
            lbl = Label(text=item, font_size='18sp', color=(0.7, 0.7, 0.7, 1))
            self.labels.append(lbl)
            self.layout.add_widget(lbl)

        # Инфо
        self.status = Label(
            text='Use VOL↑/VOL↓ to move, POWER to select',
            font_size='14sp',
            color=(0.4, 0.8, 1, 1),
            size_hint=(1, 0.15)
        )
        self.layout.add_widget(self.status)

        self.add_widget(self.layout)

        # Проверяем батарею каждые 2 секунды
        Clock.schedule_interval(self.check_battery, 2)

        # Обработка кнопок
        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_interval(self.update_menu, 0.1)

    def move_up(self):
        self.selected = (self.selected - 1) % len(self.menu_items)

    def move_down(self):
        self.selected = (self.selected + 1) % len(self.menu_items)

    def update_menu(self, *args):
        for i, lbl in enumerate(self.labels):
            if i == self.selected:
                lbl.text = f"> {self.menu_items[i]}"
                lbl.color = (0, 1, 1, 1)
            else:
                lbl.text = f"  {self.menu_items[i]}"
                lbl.color = (0.7, 0.7, 0.7, 1)

    def select_option(self):
        choice = self.menu_items[self.selected]
        self.status.text = f"Selected: {choice}"
        if choice == "Power off":
            self.status.text = "Shutting down..."
        elif choice == "Reboot system now":
            self.status.text = "Rebooting..."
        elif choice == "Apply update from ADB":
            self.status.text = "Waiting for ADB sideload..."
        elif choice == "Wipe data/factory reset":
            self.status.text = "Formatting /data..."
        elif choice == "Wipe cache partition":
            self.status.text = "Clearing cache..."

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key in (24, 273):  # VOL UP / стрелка вверх
            self.move_up()
        elif key in (25, 274):  # VOL DOWN / стрелка вниз
            self.move_down()
        elif key in (26, 13, 32):  # POWER / Enter / Пробел
            self.select_option()

    def check_battery(self, *args):
        info = battery.status
        if info and info.get('isCharging'):
            self.status.text = "⚡ Cable connected — switching to Sensor Recovery..."
            Clock.schedule_once(self.go_sensor, 1)

    def go_sensor(self, *args):
        self.manager.current = 'sensor'


# ---------- Сенсорный Recovery ----------
class SensorRecovery(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=25, spacing=10)

        self.title = Label(
            text='[b]Sensor Recovery Mode[/b]',
            markup=True,
            font_size='26sp',
            color=(0, 0.9, 1, 1),
            size_hint=(1, 0.2)
        )
        self.layout.add_widget(self.title)

        # Кнопки Recovery
        actions = [
            ("Wipe Data", lambda: self.show_status("Wiping /data...")),
            ("Backup", lambda: self.show_status("Creating backup...")),
            ("Restore", lambda: self.show_status("Restoring backup...")),
            ("Reboot System", lambda: self.show_status("Rebooting...")),
            ("← Back", self.go_back)
        ]

        for text, func in actions:
            btn = Button(
                text=text,
                font_size='20sp',
                background_color=(0.1, 0.4, 1, 1),
                size_hint=(1, 0.18)
            )
            btn.bind(on_release=lambda x, f=func: f())
            self.layout.add_widget(btn)

        self.status = Label(text='', font_size='16sp', color=(0.6, 0.9, 1, 1))
        self.layout.add_widget(self.status)
        self.add_widget(self.layout)

        Clock.schedule_interval(self.check_battery, 2)

    def show_status(self, msg):
        self.status.text = msg

    def go_back(self, *args):
        self.manager.current = 'classic'

    def check_battery(self, *args):
        info = battery.status
        if info and not info.get('isCharging'):
            self.status.text = "🔌 Cable disconnected — returning to Classic Recovery..."
            Clock.schedule_once(self.go_back, 1)


# ---------- Основное приложение ----------
class RecoveryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(ClassicRecovery(name='classic'))
        sm.add_widget(SensorRecovery(name='sensor'))
        return sm


if __name__ == '__main__':
    RecoveryApp().run()
