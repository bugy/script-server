#!/usr/bin/python3

import time

lines_count = 10000
total_bytes = 130480561
progress_max_width = 24

print('Print some progress bar')
print('With %d lines in total' % (lines_count))
print('\n')

for i in range(0, lines_count):
    width = int(i * progress_max_width / lines_count)
    progress = '|' + ('=' * width) + '>' + (' ' * (progress_max_width - width)) + '|'

    bytes = i * total_bytes / lines_count
    bytes_percent = float(i * 100) / lines_count
    print("%s Got %d bytes of %d (%.2f%%)\r" % (progress, bytes, total_bytes, bytes_percent), end='')
    time.sleep(0.001)
