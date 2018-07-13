#!/usr/bin/python

import os
import pygame
import time
from time import sleep

print os.geteuid()
pygame.init()
pygame.mixer.music.load("beep.wav")
pygame.mixer.music.play()
sleep(1)