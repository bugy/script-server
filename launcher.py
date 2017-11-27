#!/usr/bin/env python3

import os, sys

sys.path.append("src")
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import server

server.main()
