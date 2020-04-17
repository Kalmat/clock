#!/usr/bin/python3
# -*- coding: utf-8 -*-

__version__ = "2.0.1"

"""
********* TRANSPARENT CLOCK by alef ********* 
This is just a transparent, always-on-top, movable, count-down/alarm digital clock

I couldn't find anything similar, so I decided to code it!
Feel free to use it, modify it, distribute it or whatever... just be sure to mention me... well, nothing really. 

*** USAGE:
MOVE WINDOW:    m or Home+MouseLeft or Alt+F7
QUIT PROGRAM:   Escape
ALARM           a (set alarm) / s (cancel alarm)
TIMER:          c (activate counter) / s (stop counter)
TITLE BAR:      t
OTHER OPTIONS:  Home+MouseRight

*** TRANSPARENT WINDOW BASED ON (Thanks to):
ZetCode PyCairo tutorial

This code example shows how to create a transparent window.

author: Jan Bodnar
website: zetcode.com
last edited: August 2012
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import cairo
import os
import platform
import time
import plyer
import playsound
import threading


def get_resource_path(rel_path):
    """ Thanks to: detly < https://stackoverflow.com/questions/4416336/adding-a-program-icon-in-python-gtk/4416367 > """
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource


class MyWindow(Gtk.Window):

    def __init__(self):
        super(MyWindow, self).__init__()

        self.archOS = platform.system()

        self.connect("draw", self.on_draw)
        self.connect("enter-notify-event", self.on_hover_in)
        self.connect("leave-notify-event", self.on_hover_out)
        self.connect("key-press-event", self.on_key_press)
        self.connect("delete-event", lambda y, z: Gtk.main_quit())

        self.tran_setup()
        self.set_title("Clock by alef")
        self.set_icon_from_file(get_resource_path("resources/clock.ico"))
        # self.set_size_request(400, 400)  # Not needed. Window will resize automatically
        self.set_resizable(False)          # Comment this if you want a resizable window (text size will not change)
        if "Linux" in self.archOS:
            self.set_decorated(False)      # On windows you need the title bar to move the window
        self.set_keep_above(True)          # Comment to avoid "always on top" behavior (or Home+Right-Mouse while running)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.clock_mode = True
        self.allow_quit = True
        self.alarm_set = False
        self.counter_set = False
        self.time_label = None
        self.font = "light 40"
        self.font_color = "white"
        self.tooltip = "MOVE:    Home+MouseLeft\nQUIT:        Escape\nALARM:   a / s\nTIMER:     c / s\nTITLE:       t\nOTHER:    Home+MouseRight"
        self.minutes = 5
        self.init_minutes = 5
        self.init_seconds = 0
        self.seconds = 0
        self.time_label = None
        self.hh_alarm = ""
        self.mm_alarm = ""
        self.timer = None
        self.beep_sound = get_resource_path("resources/beep.wav")
        self.P = None

        self.time_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.time_label.set_homogeneous(False)
        self.change_time_label_color(self.font_color)
        self.time_label.modify_font(Pango.FontDescription(self.font))
        self.add(self.time_label)

        self.label = Gtk.Label()
        self.label.set_tooltip_text(self.tooltip)
        self.label.set_justify(Gtk.Justification.CENTER)

        self.alarm_image = Gtk.Image()
        self.alarm_image.set_from_file(get_resource_path("resources/Alarm_set.png"))
        self.alarm_not_set_image = Gtk.Image()
        self.alarm_not_set_image.set_from_file(get_resource_path("resources/Alarm_not_set.png"))
        self.image = None

        self.hour_alarm = Gtk.Entry()
        self.hour_alarm.set_width_chars(2)
        self.hour_alarm.set_max_length(2)
        self.hour_alarm.modify_font(Pango.FontDescription(self.font))
        self.hour_alarm.set_text("00")
        self.hour_alarm.set_visibility(True)

        self.min_alarm = Gtk.Entry()
        self.min_alarm.set_width_chars(2)
        self.min_alarm.set_max_length(2)
        self.min_alarm.modify_font(Pango.FontDescription(self.font))
        self.min_alarm.set_text("00")
        self.min_alarm.set_visibility(True)

        self.min_entry = Gtk.Entry()
        self.min_entry.set_width_chars(2)
        self.min_entry.set_max_length(2)
        self.min_entry.modify_font(Pango.FontDescription(self.font))
        self.min_entry.set_text("10")
        self.min_entry.set_visibility(True)

        self.values_label = Gtk.Label()
        self.values_label.modify_font(Pango.FontDescription(self.font))
        self.values_label.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse("white"))
        self.values_label.set_text(":")
        self.values_label.set_justify(Gtk.Justification.CENTER)

        self.sec_entry = Gtk.Entry()
        self.sec_entry.set_width_chars(2)
        self.sec_entry.set_max_length(2)
        self.sec_entry.modify_font(Pango.FontDescription(self.font))
        self.sec_entry.set_text("00")
        self.sec_entry.set_visibility(True)

        self.draw_clock()
        self.start_timer()

    def tran_setup(self):
        self.set_app_paintable(True)
        screen = self.get_screen()

        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

    def draw_clock(self):
        self.allow_quit = True

        if self.label not in self.time_label.get_children():
            self.time_label.pack_start(self.label, expand=True, fill=True, padding=10)

        if self.alarm_set:
            if self.image not in self.time_label.get_children():
                self.image = self.alarm_image
                self.alarm_image.set_tooltip_text(str(self.hh_alarm) + ":" + str(self.mm_alarm))
                self.time_label.pack_end(self.image, expand=True, fill=True, padding=0)
        else:
            # Change this part to always show the alarm icon (enabled or disabled)
            if self.image in self.time_label.get_children():
                # self.image = self.alarm_not_set_image
                # self.alarm_image.set_tooltip_text("")
                self.time_label.remove(self.image)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        if self.clock_mode:
            if self.alarm_set:
                self.check_alarm(current_time)
        elif self.counter_set:
            self.check_countdown()
            if self.counter_set:
                current_time = "00:" + str(format(self.minutes, "02d")) + ":" + str(format(self.seconds, "02d"))

        self.label.set_text(current_time)

        self.show_all()

        return True

    def remove_time_label(self):
        if self.label in self.time_label.get_children():
            self.time_label.remove(self.label)

    def change_time_label_color(self, font_color="white"):
        self.font_color = font_color
        self.time_label.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse(font_color))

    def get_countdown_values(self):

        self.stop_timer()
        self.remove_time_label()

        self.time_label.pack_start(self.min_entry, expand=True, fill=True, padding=0)
        self.time_label.pack_start(self.values_label, expand=True, fill=True, padding=0)
        self.time_label.pack_start(self.sec_entry, expand=True, fill=True, padding=0)

        self.min_entry.grab_focus()

        self.show_all()

    def start_countdown(self, minutes, seconds):
        self.minutes = int(minutes)
        self.seconds = int(seconds) + 1
        if self.seconds > 59:
            self.seconds = 59
        self.init_minutes = self.minutes
        self.init_seconds = self.seconds - 1

        self.remove_counter_values()
        self.draw_clock()
        self.start_timer()

    def check_countdown(self):
        if self.seconds == 0:
            if self.minutes == 0:
                self.clock_mode = True
                self.counter_set = False
            else:
                self.seconds = 59
                self.minutes -= 1
        else:
            self.seconds -= 1

        if self.seconds == 0 and self.minutes == 0 and self.counter_set:
            self.notify()

    def remove_counter_values(self):
        if self.min_entry in self.time_label.get_children():
            self.time_label.remove(self.min_entry)
        if self.values_label in self.time_label.get_children():
            self.time_label.remove(self.values_label)
        if self.sec_entry in self.time_label.get_children():
            self.time_label.remove(self.sec_entry)
        self.min_entry.set_text("10")
        self.sec_entry.set_text("00")

    def get_alarm_values(self):

        self.stop_timer()
        self.remove_time_label()

        self.time_label.pack_start(self.hour_alarm, expand=True, fill=True, padding=0)
        self.time_label.pack_start(self.values_label, expand=True, fill=True, padding=0)
        self.time_label.pack_start(self.min_alarm, expand=True, fill=True, padding=0)

        self.hour_alarm.grab_focus()

        self.show_all()

    def start_alarm(self):
        self.remove_alarm_values()
        self.draw_clock()
        self.start_timer()

    def check_alarm(self, current_time):
        if self.hh_alarm + ":" + self.mm_alarm == current_time[:5] and current_time[-2:] == "00":
            self.notify()
            self.clock_mode = True
            self.alarm_set = False

    def remove_alarm_values(self):
        if self.hour_alarm in self.time_label.get_children():
            self.time_label.remove(self.hour_alarm)
        if self.values_label in self.time_label.get_children():
            self.time_label.remove(self.values_label)
        if self.min_alarm in self.time_label.get_children():
            self.time_label.remove(self.min_alarm)
        self.hour_alarm.set_text("00")
        self.min_alarm.set_text("00")

    def notify(self):
        if self.alarm_set:
            message = "Your alarm time has arrived!!!"
        elif self.counter_set:
            message = "Your countdown for %02d:%02d finished!!!" % (self.init_minutes, self.init_seconds)
        else:
            message = "Don't know what happened nor why you're watching this"

        plyer.notification.notify(
            title='Clock by alef',
            message=message,
            app_icon="resources/clock.ico",
            timeout=5,
        )

        t = threading.Thread(target=self.beep)
        t.start()

    def beep(self):
        playsound.playsound(self.beep_sound)

    def start_timer(self):
        if self.timer is None:
            self.timer = GLib.timeout_add(1000, self.draw_clock)   # This will invoke draw_clock every second

    def stop_timer(self):
        if self.timer is not None:
            GLib.source_remove(self.timer)
            self.timer = None

    def on_draw(self, widget, event):
        event.set_source_rgba(0.2, 0.2, 0.2, 0.4)
        event.set_operator(cairo.OPERATOR_SOURCE)
        event.paint()

    def on_hover_in(self, widget, event):
        self.change_time_label_color("grey")

    def on_hover_out(self, widget, event):
        self.change_time_label_color("white")

    def on_key_press(self, widget, event):
        # check values at https://gitlab.gnome.org/GNOME/gtk/raw/master/gdk/gdkkeysyms.h (without leading 'GDK_KEY_')
        if event.keyval == Gdk.keyval_from_name("Escape"):      # Escape --> QUIT
            if self.allow_quit:
                Gtk.main_quit()
            else:
                self.clock_mode = True
                self.counter_set = False
                self.alarm_set = False
                self.allow_quit = True
                self.remove_counter_values()
                self.remove_alarm_values()
                self.draw_clock()
                self.start_timer()

        elif event.keyval == Gdk.keyval_from_name("t"):         # t, T --> Add / Remove TITLE BAR
            if self.clock_mode:
                if "Windows" not in self.archOS:
                    self.set_decorated(not self.get_decorated())

        elif event.keyval == Gdk.keyval_from_name("c"):         # c, C --> Counter mode
            if self.clock_mode:
                self.clock_mode = False
                self.counter_set = True
                self.allow_quit = False
                event.keyval = 0
                self.get_countdown_values()

        elif event.keyval == Gdk.keyval_from_name("a"):         # a, A --> Alarm mode
            if self.clock_mode:
                self.clock_mode = True
                self.alarm_set = True
                self.allow_quit = False
                event.keyval = 0
                self.get_alarm_values()

        elif event.keyval == Gdk.keyval_from_name("s"):         # s, S --> STOP Countdown / Alarm
            self.clock_mode = True
            self.counter_set = False
            self.alarm_set = False
            self.remove_time_label()
            self.draw_clock()

        elif event.keyval == Gdk.keyval_from_name("Return"):    # Return --> Gather Countdown / Alarm values
            if self.counter_set:
                proceed = True
                minutes = self.min_entry.get_text()
                if not minutes.isdigit():
                    self.min_entry.set_text("")
                    self.min_entry.grab_focus()
                    proceed = False
                seconds = self.sec_entry.get_text()
                if not seconds.isdigit() or int(seconds) > 59:
                    self.sec_entry.set_text("")
                    self.sec_entry.grab_focus()
                    proceed = False
                if proceed:
                    self.start_countdown(minutes, seconds)
            elif self.alarm_set:
                proceed = True
                self.hh_alarm = self.hour_alarm.get_text()
                if not self.hh_alarm.isdigit() or int(self.hh_alarm) > 23:
                    self.hour_alarm.set_text("")
                    self.hour_alarm.grab_focus()
                    proceed = False
                self.mm_alarm = self.min_alarm.get_text()
                if not self.mm_alarm.isdigit() or int(self.mm_alarm) > 59:
                    self.min_alarm.set_text("")
                    self.min_alarm.grab_focus()
                    proceed = False
                if proceed:
                    self.start_alarm()


def main():
    MyWindow()
    Gtk.main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        exit()
