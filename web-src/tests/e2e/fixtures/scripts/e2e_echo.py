#!/usr/bin/env python3
"""E2E fixture script: echoes its arguments and prints a few output lines.

Used by the Playwright suite to verify the full execution path
(XSRF POST -> process spawn -> websocket streaming -> log panel rendering).
"""
import sys
import time

print('e2e: started')
print('e2e: args = ' + ' '.join(sys.argv[1:]))
sys.stdout.flush()

time.sleep(0.2)
print('e2e: working...')
sys.stdout.flush()

time.sleep(0.2)
print('e2e: done')
