import os
import sys

output_file = sys.argv[1]

with open(output_file, 'w') as f:
    for arg in sys.argv[2:]:
        f.write(arg + '\n')

    f.write('\n\n')

    fields = ['event_type', 'execution_id', 'pid', 'script_name', 'user', 'exit_code']

    for field in fields:
        value = os.environ.get(field)

        f.write(field + ': ' + str(value) + '\n')
