#!/usr/bin/env python3
import sys

# getmonitor.py is used to retrieve the monitor values
# using Zabbix system.run[]


def get(env, command):
    try:
        with open(f'status/{env}.log', 'r') as f:
            time = f.readline()
            test = f.readline()
            login = f.readline()
            if command == 'time':
                return time.strip()
            elif command == 'test':
                return test.strip()
            elif command == 'login':
                return login.strip()
            elif command == 'pam':
                return login.strip()
    except Exception:
        return "error\n"


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(sys.argv[0] + "  <env> <command>")
    env = sys.argv[1]
    command = sys.argv[2]
    print(get(env, command))
