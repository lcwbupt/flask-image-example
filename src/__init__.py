from __future__ import print_function
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

from .server import app

class Config(object):
  DEBUG = False
  SESSION_TYPE = 'filesystem'

app.config.from_object(Config)
