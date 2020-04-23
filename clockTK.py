#!/usr/bin/python3
# -*- coding: utf-8 -*-

__version__ = "3.0.0"

"""
********* TRANSPARENT CLOCK by alef ********* 
This is just a transparent, always-on-top, movable, count-down/alarm digital clock

I couldn't find anything similar, so I decided to code it!
Feel free to use it, modify it, distribute it or whatever... just be sure to mention me... well, nothing really. 

*** USAGE:
MOVE WINDOW:    Home+MouseLeft (Linux / Unity only)
QUIT PROGRAM:   Escape
ALARM           a (set alarm) / s (cancel alarm) - hh:mm
TIMER:          c (initiate counter) / s (stop counter) - mm:ss
TITLE BAR:      t (on / off - on Win you will need the title bar to move the clock)
OTHER OPTIONS:  Home+MouseRight (Linux / Unity only)
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


class MyWindow(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # General variables
        self.archOS = platform.system()
        self.timer = None
        self.gathering_values = False
        self.decorated = False
        self.allow_quit = True
        self.alarm_set = False
        self.counter_set = False
        self.time_label = None
        self.bg_color = "gray19"
        self.font = "Helvetica"
        self.font_size = int(38 * (self.parent.winfo_screenwidth() / 1920))
        self.font_color = "white"
        self.tooltip = "MOVE:    Home+MouseLeft\n" \
                       "QUIT:      Escape\n" \
                       "ALARM:   a / s (hh:mm)\n" \
                       "TIMER:     c / s (mm:ss)\n" \
                       "TITLE:       t\n" \
                       "OTHER:    Home+MouseRight"
        self.minutes = 10
        self.init_minutes = 10
        self.init_seconds = 0
        self.seconds = 0
        self.time_label = None
        self.hh_alarm = ""
        self.mm_alarm = ""
        self.timer = None
        self.beep_sound = get_resource_path("resources/beep.wav")

        # Window attributes
        self.parent.title("Clock by alef")
        if "Windows" in self.archOS:
            self.parent.icon(get_resource_path("resources/clock.ico"))
        else:
            img = ImageTk.PhotoImage(file=get_resource_path("resources/clock.ico"))
            self.parent.tk.call('wm', 'iconphoto', self.parent._w, img)

        self.parent.bind('<KeyRelease>', self.on_key_press)
        self.parent.bind('<Button-1>', self.on_enter)
        self.parent.bind('<Button-2>', self.on_enter)

        self.parent.wait_visibility(self.parent)
        self.parent.configure(bg=self.bg_color)
        self.parent.wm_attributes("-alpha", 0.6)
        if "Windows" in self.archOS:
            self.parent.overrideredirect(True)
            self.parent.attributes('-topmost', True)
            self.parent.resizable(False, False)
        else:
            self.parent.attributes("-type", "dock")

        # Widgets
        self.label = tk.Label(self.parent, bg=self.bg_color, font=(self.font, self.font_size), fg=self.font_color)
        tt.Tooltip(self.label, text=self.tooltip)

        img = ImageTk.PhotoImage(file=get_resource_path("resources/Alarm_set.png"))
        self.alarm_image = tk.Label(image=img, bg=self.bg_color)
        self.alarm_image.image = img
        self.alarm_tt = tt.Tooltip(self.alarm_image, text="")

        img = ImageTk.PhotoImage(file=get_resource_path("resources/Alarm_not_set.png"))
        self.alarm_not_set_image = tk.Label(image=img, bg=self.bg_color)
        self.alarm_not_set_image.image = img

        self.get_hour = tk.Entry(font=self.font+" "+str(self.font_size), width=2)
        self.vcmd_hour = (self.register(self.on_validate_hour), "%P")
        self.get_hour.configure(validate="key", validatecommand=self.vcmd_hour)
        tt.Tooltip(self.get_hour, text="Enter hours (HH)")

        self.values_label = tk.Label(self.parent, bg=self.bg_color, text=":", font=(self.font, self.font_size), fg=self.font_color)

        self.get_min = tk.Entry(font=self.font+" "+str(self.font_size), width=2)
        self.vcmd_min_sec = (self.register(self.on_validate_min_sec), "%P")
        self.get_min.configure(validate="key", validatecommand=self.vcmd_min_sec)
        tt.Tooltip(self.get_min, text="Enter minutes (MM)")

        self.get_sec = tk.Entry(font=self.font+" "+str(self.font_size), width=2)
        self.get_sec.configure(validate="key", validatecommand=self.vcmd_min_sec)
        tt.Tooltip(self.get_sec, text="Enter seconds (SS)")

        # Start program loop
        self.draw_clock()

    def draw_clock(self):
        self.allow_quit = True

        current_time = time.strftime("%H:%M:%S")
        if self.alarm_set:
            self.check_alarm(current_time)
        elif self.counter_set:
            self.check_counter()
            if self.counter_set:
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

        self.timer = self.parent.after(1000 - int(divmod(time.time(), 1)[1] * 1000), self.draw_clock)

    def remove_time_label(self):
        if self.label.grid_info():
            self.label.grid_remove()

    def stop_timer(self):
        self.parent.after_cancel(self.timer)
        self.timer = None

    def get_alarm_values(self):
        self.get_hour.configure(validate="key", validatecommand=self.vcmd_hour)
        self.get_min.configure(validate="key", validatecommand=self.vcmd_min_sec)
        self.remove_time_label()
        self.stop_timer()

        self.get_hour.delete(0, 'end')
        self.get_hour.insert(0, '00')
        self.get_hour.grid(row=0, column=0)
        self.values_label.grid(row=0, column=1)
        self.get_min.delete(0, 'end')
        self.get_min.insert(0, '00')
        self.get_min.grid(row=0, column=2)

        self.get_hour.select_range(0, 'end')
        self.get_hour.icursor('end')
        self.get_hour.focus_force()

    def remove_alarm_values(self):
        self.get_hour.grid_remove()
        self.values_label.grid_remove()
        self.get_min.grid_remove()

    def start_alarm(self):
        self.get_hour.configure(validate="key", validatecommand="")
        self.get_min.configure(validate="key", validatecommand="")
        self.remove_alarm_values()
        self.draw_clock()

    def check_alarm(self, current_time):
        if self.hh_alarm + ":" + self.mm_alarm + ":" + "00" == current_time:
            self.beep()
            self.alarm_set = False

    def get_counter_values(self):
        self.get_min.configure(validate="key", validatecommand=self.vcmd_min_sec)
        self.get_sec.configure(validate="key", validatecommand=self.vcmd_min_sec)

        self.remove_time_label()
        self.stop_timer()

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

    def remove_counter_values(self):
        self.get_min.grid_remove()
        self.values_label.grid_remove()
        self.get_sec.grid_remove()

    def start_counter(self, minutes, seconds):
        self.get_min.configure(validate="key", validatecommand="")
        self.get_sec.configure(validate="key", validatecommand="")

        self.remove_counter_values()

        self.init_minutes = minutes
        self.init_seconds = seconds
        self.minutes = int(minutes)
        self.seconds = int(seconds) + 1

        self.draw_clock()

    def check_counter(self):
        if self.seconds == 0:
            if self.minutes == 0:
                self.counter_set = False
            else:
                self.seconds = 59
                self.minutes -= 1
        else:
            self.seconds -= 1

        if self.minutes == 0 and self.seconds == 0 and self.counter_set:
            self.beep()

    def beep(self):
        if self.alarm_set:
            message = "Your alarm time has arrived!!!"
        elif self.counter_set:
            message = "Your countdown for %s:%s finished!!!" % (self.init_minutes, self.init_seconds)
        else:
            message = "Oops, don't know why you're watching this. Likely, something went wrong :("

        t = threading.Thread(target=notify, args=(message, self.beep_sound))
        t.start()

    def on_enter(self, e):
        e.widget.focus_force()

    def on_validate_hour(self, new_value):
        if (self.alarm_set or self.counter_set) and new_value.strip():
            try:
                value = int(new_value)
                if value < 0 or value > 23:
                    self.bell()
                    return False
            except ValueError:
                self.bell()
                return False

        return True

    def on_validate_min_sec(self, new_value):
        if (self.alarm_set or self.counter_set) and new_value.strip():
            try:
                value = int(new_value)
                if value < 0 or value > 59:
                    self.bell()
                    return False
            except ValueError:
                self.bell()
                return False

        return True

    def on_key_press(self, e):
        if e.keysym == "Escape":      # Escape --> QUIT
            if self.allow_quit:
                self.parent.destroy()
            else:
                if self.counter_set:
                    self.counter_set = False
                    self.remove_counter_values()
                if self.alarm_set:
                    self.alarm_set = False
                    self.remove_alarm_values()
                self.allow_quit = True
                self.draw_clock()

        elif e.keysym in ("t", "T"):         # t, T --> Add / Remove TITLE BAR
            if not self.alarm_set and not self.counter_set:
                if self.decorated:
                    if "Windows" in self.archOS:
                        self.parent.overrideredirect(True)
                    else:
                        self.parent.attributes('-type', 'dock')
                else:
                    if "Windows" in self.archOS:
                        self.parent.overrideredirect(False)
                    else:
                        self.parent.attributes('-type', 'normal')
                        self.parent.resizable(False, False)

                self.decorated = not self.decorated

        elif e.keysym in ("a", "A"):  # a, A --> Alarm mode
            if not self.alarm_set and not self.counter_set:
                self.alarm_set = True
                self.allow_quit = False
                self.get_alarm_values()

        elif e.keysym in ("c", "C"):         # c, C --> Counter mode
            if not self.alarm_set and not self.counter_set:
                self.counter_set = True
                self.allow_quit = False
                self.get_counter_values()

        elif e.keysym in ("s", "S"):         # s, S --> STOP Countdown / Alarm
            self.counter_set = False
            self.alarm_set = False

        elif e.keysym == "Return":    # Return --> Gather Countdown / Alarm values
            if self.alarm_set:
                self.hh_alarm = str(format(int(self.get_hour.get()), "02d"))
                self.mm_alarm = str(format(int(self.get_min.get()), "02d"))
                self.start_alarm()
            elif self.counter_set:
                minutes = self.get_min.get()
                seconds = self.get_sec.get()
                if int(minutes) != 0 or int(seconds) != 0:
                    self.start_counter(minutes, seconds)


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
    root = tk.Tk()
    MyWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
