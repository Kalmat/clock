#!/usr/bin/python3
# -*- coding: utf-8 -*-

__version__ = "3.0.0"

"""
********* TRANSPARENT CLOCK by alef *********
This is just a transparent, always-on-top, movable, count-down/alarm digital clock

I couldn't find anything similar, so I decided to code it!
Feel free to use it, modify it, distribute it or whatever... just be sure to mention me... well, nothing really.

*** USAGE:
QUIT PROGRAM:       Escape
SET ALARM:          a / A (hh:mm)
SET TIMER:          t / T (mm:ss)
STOP ALARM/TIMER:   s / S
MOVE WINDOW:        Mouse Button-1
"""

import platform
import os
import time
import tkinter as tk
from PIL import ImageTk
import plyer
import playsound
import threading
import tktooltip as tt


class FakeRoot(tk.Tk):
    # (Author: noob oddy) https://stackoverflow.com/questions/4066027/making-tkinter-windows-show-up-in-the-taskbar

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Clock by alef")
        self.wm_title("Clock by alef")
        img = ImageTk.PhotoImage(file=get_resource_path("resources/clock.ico"))
        self.tk.call('wm', 'iconphoto', self._w, img)
        self.wait_visibility(self)
        self.configure(bg="black")
        self.attributes('-alpha', 0.0)
        self.geometry("1x1+0+0")
        self.lower()
        self.iconify()


class MyWindow(tk.Toplevel):

    def __init__(self, master, *args, **kwargs):
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.master = master

        # General variables
        self.archOS = platform.system()
        self.callback_job = None
        self.gathering_values = False
        self.decorated = False
        self.clock_mode = True
        self.alarm_set = False
        self.timer_set = False
        self.time_label = None
        self.bg_color = "gray19"
        self.font = "Helvetica"
        self.font_size = int(38 * (self.winfo_screenwidth() / 1920))
        self.font_color = "white"
        self.tooltip = "Click on clock to enter a command:\n" \
                       "QUIT:\tEscape\n" \
                       "ALARM:\ta (hh:mm)\n" \
                       "TIMER:\tt (mm:ss)\n" \
                       "STOP:\ts (alarm / timer)\n" \
                       "MOVE:\tMouse Button-1"
        self.minutes = 10
        self.init_minutes = 10
        self.init_seconds = 0
        self.seconds = 0
        self.time_label = None
        self.hh_alarm = ""
        self.mm_alarm = ""
        self.callback_job = None
        self.beep_sound = get_resource_path("resources/beep.wav")
        self.mouse_X_pos = 0
        self.mouse_Y_pos = 0

        # Entry validation functions
        self.vcmd_hour = (self.register(self.on_validate_hour), "%P")
        self.vcmd_min_sec = (self.register(self.on_validate_min_sec), "%P")

        self.wait_visibility(self)
        self.configure(bg=self.bg_color)
        self.wm_attributes("-alpha", 0.6)
        if "Windows" in self.archOS:
            self.overrideredirect(True)
            self.attributes('-topmost', True)
            self.resizable(False, False)
        else:
            self.attributes("-type", "dock")

        # Widgets
        self.label = tk.Label(self, bg=self.bg_color, font=(self.font, self.font_size), fg=self.font_color)
        tt.Tooltip(self.label, text=self.tooltip)

        img = ImageTk.PhotoImage(file=get_resource_path("resources/Alarm_set.png"))
        self.alarm_image = tk.Label(self, image=img, bg=self.bg_color)
        self.alarm_image.image = img
        self.alarm_tt = tt.Tooltip(self.alarm_image, text="")

        # Not used at the moment
        # img = ImageTk.PhotoImage(file=get_resource_path("resources/Alarm_not_set.png"))
        # self.alarm_not_set_image = tk.Label(image=img, bg=self.bg_color)
        # self.alarm_not_set_image.image = img

        self.get_hour = tk.Entry(self, font=self.font+" "+str(self.font_size), width=2)
        tt.Tooltip(self.get_hour, text="Enter hours (HH)")

        self.values_label = tk.Label(self, bg=self.bg_color, text=":", font=(self.font, self.font_size), fg=self.font_color)

        self.get_min = tk.Entry(self, font=self.font+" "+str(self.font_size), width=2)
        tt.Tooltip(self.get_min, text="Enter minutes (MM)")

        self.get_sec = tk.Entry(self, font=self.font+" "+str(self.font_size), width=2)
        tt.Tooltip(self.get_sec, text="Enter seconds (SS)")

        # Event bindings
        self.bind('<KeyRelease>', self.on_key_press)
        self.bind('<Button-1>', self.on_enter)
        self.bind('<Button-2>', self.on_enter)
        self.label.bind('<B1-Motion>', self.on_motion)
        self.label.bind('<Button-1>', self.on_button_click)
        self.label.bind('<ButtonRelease-1>', self.on_button_release)

        # Start program loop
        self.draw_clock()

    def draw_clock(self):
        self.clock_mode = True

        current_time = time.strftime("%H:%M:%S")
        if self.alarm_set:
            self.check_alarm(current_time)
        elif self.timer_set:
            self.check_timer()
            if self.timer_set:
                current_time = "00:" + str(format(self.minutes, "02d")) + ":" + str(format(self.seconds, "02d"))
        self.label.configure(text=current_time)

        if not self.label.grid_info():
            self.label.grid(row=0, column=0)

        if self.alarm_set:
            if not self.alarm_image.grid_info():
                self.alarm_image.grid(row=0, column=1)
                self.alarm_tt.text = self.hh_alarm + ":" + self.mm_alarm
        else:
            if self.alarm_image.grid_info():
                self.alarm_image.grid_remove()

        self.callback_job = self.after(1000 - int(divmod(time.time(), 1)[1] * 1000), self.draw_clock)

    def remove_time_label(self):
        if self.label.grid_info():
            self.label.grid_remove()

    def stop_callback(self):
        if self.callback_job:
            self.after_cancel(self.callback_job)
            self.callback_job = None

    def get_alarm_values(self):
        self.set_key_validators(on=True)
        self.remove_time_label()
        self.stop_callback()
        self.clock_mode = False

        self.get_hour.delete(0, 'end')
        self.get_hour.insert(0, time.strftime("%H"))
        self.get_hour.grid(row=0, column=0)
        self.values_label.grid(row=0, column=1)
        self.get_min.delete(0, 'end')
        self.get_min.insert(0, time.strftime("%M"))
        self.get_min.grid(row=0, column=2)

        self.get_hour.select_range(0, 'end')
        self.get_hour.icursor('end')
        self.get_hour.focus_force()

    def remove_alarm_values(self):
        self.get_hour.grid_remove()
        self.values_label.grid_remove()
        self.get_min.grid_remove()
        self.set_key_validators(on=False)

    def start_alarm(self):
        self.remove_alarm_values()
        self.draw_clock()

    def check_alarm(self, current_time):
        if self.hh_alarm + ":" + self.mm_alarm + ":" + "00" == current_time:
            self.beep()
            self.alarm_set = False

    def get_timer_values(self):
        self.set_key_validators(on=True)
        self.remove_time_label()
        self.stop_callback()
        self.clock_mode = False

        self.get_min.delete(0, 'end')
        self.get_min.insert(0, '10')
        self.get_min.grid(row=0, column=0)
        self.values_label.grid(row=0, column=1)
        self.get_sec.delete(0, 'end')
        self.get_sec.insert(0, '00')
        self.get_sec.grid(row=0, column=2)

        self.get_min.select_range(0, 'end')
        self.get_min.icursor('end')
        self.get_min.focus_force()

    def remove_timer_values(self):
        self.get_min.grid_remove()
        self.values_label.grid_remove()
        self.get_sec.grid_remove()
        self.set_key_validators(on=False)

    def start_timer(self, minutes, seconds):
        self.remove_timer_values()

        self.init_minutes = minutes
        self.init_seconds = seconds
        self.minutes = int(minutes)
        self.seconds = int(seconds) + 1

        self.draw_clock()

    def check_timer(self):
        if self.seconds == 0:
            if self.minutes == 0:
                self.timer_set = False
            else:
                self.seconds = 59
                self.minutes -= 1
        else:
            self.seconds -= 1

        if self.minutes == 0 and self.seconds == 0 and self.timer_set:
            self.beep()

    def beep(self):
        if self.alarm_set:
            message = "Your alarm time has arrived!!!"
        elif self.timer_set:
            message = "Your countdown for %s:%s finished!!!" % (self.init_minutes, self.init_seconds)
        else:
            message = "Oops, don't know why you're watching this. Likely, something went wrong :("

        t = threading.Thread(target=notify, args=(message, self.beep_sound))
        t.start()

    def on_enter(self, e):
        e.widget.focus_force()

    def on_motion(self, e):
        self.geometry('+{0}+{1}'.format(e.x_root - self.mouse_X_pos, e.y_root - self.mouse_Y_pos))

    def on_button_click(self, e):
        self.mouse_X_pos = e.x
        self.mouse_Y_pos = e.y

    def on_button_release(self, e):
        self.mouse_X_pos = 0
        self.mouse_Y_pos = 0

    def set_key_validators(self, on=True):
        if on:
            self.get_hour.configure(validate="key", validatecommand=self.vcmd_hour)
            self.get_min.configure(validate="key", validatecommand=self.vcmd_min_sec)
            self.get_sec.configure(validate="key", validatecommand=self.vcmd_min_sec)
        else:
            self.get_hour.configure(validate="key", validatecommand="")
            self.get_min.configure(validate="key", validatecommand="")
            self.get_sec.configure(validate="key", validatecommand="")

    def on_validate_hour(self, new_value):
        if not self.clock_mode and new_value.strip():
            try:
                value = int(new_value)
                if value < 0 or value > 23 or len(new_value) > 2:
                    self.bell()
                    return False
            except ValueError:
                self.bell()
                return False

        return True

    def on_validate_min_sec(self, new_value):
        if not self.clock_mode and new_value.strip():
            try:
                value = int(new_value)
                if value < 0 or value > 59 or len(new_value) > 2:
                    self.bell()
                    return False
            except ValueError:
                self.bell()
                return False

        return True

    def on_key_press(self, e):
        if e.keysym == "Escape":            # Escape --> QUIT
            if self.clock_mode:
                self.master.destroy()
            else:
                if self.timer_set:
                    self.timer_set = False
                    self.remove_timer_values()
                if self.alarm_set:
                    self.alarm_set = False
                    self.remove_alarm_values()
                self.draw_clock()

        elif e.keysym in ("a", "A"):        # a, A --> Alarm mode
            if self.clock_mode:
                self.alarm_set = True
                self.get_alarm_values()

        elif e.keysym in ("t", "T"):         # t, T --> Timer mode
            if self.clock_mode:
                self.timer_set = True
                self.get_timer_values()

        elif e.keysym in ("s", "S"):         # s, S --> STOP Countdown / Alarm
            if self.clock_mode:
                self.timer_set = False
                self.alarm_set = False
                self.stop_callback()
                self.draw_clock()

        # elif e.keysym in ("m", "M"):         # m, M --> Minimize / Maximize
        #     if self.clock_mode:
        #         self.iconify()

        elif e.keysym == "Return":          # Return --> Gather Countdown / Alarm values
            if self.alarm_set:
                self.hh_alarm = str(format(int(self.get_hour.get()), "02d"))
                self.mm_alarm = str(format(int(self.get_min.get()), "02d"))
                self.start_alarm()
            elif self.timer_set:
                minutes = self.get_min.get()
                seconds = self.get_sec.get()
                if int(minutes) != 0 or int(seconds) != 0:
                    self.start_timer(minutes, seconds)


def get_resource_path(rel_path):
    """ Thanks to: detly < https://stackoverflow.com/questions/4416336/adding-a-program-icon-in-python-gtk/4416367 > """
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource


def notify(message, sound):
    if message is not None:
        plyer.notification.notify(
            title='Clock by alef',
            message=message,
            app_icon=get_resource_path("resources/clock.ico"),
            timeout=5,
        )

    if sound is not None:
        playsound.playsound(sound)


def main():
    root = FakeRoot()
    MyWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
