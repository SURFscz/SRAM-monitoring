#!/usr/bin/env python3
import sys
import json

# getmonitor.py is used to retrieve the monitor values
# using Zabbix system.run[]


def get(env, command):
    try:
        with open(f'status/{env}.log', 'r') as f:
            time = f.readline().strip()
            test = f.readline().strip()
            login = f.readline().strip()
            pam = f.readline().strip()
            if command == 'time':
                return time
            elif command == 'test':
                return test
            elif command == 'login':
                return login
            elif command == 'pam':
                return pam
            elif command == 'json':
                data = { "time": int(time), "test": test, "login": login, "pam": pam }
                return json.dumps(data)
    except Exception as e:
        return f"error: {e}\n"


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(sys.argv[0] + "  <env> <command>")
    env = sys.argv[1]
    command = sys.argv[2]
    print(get(env, command))
