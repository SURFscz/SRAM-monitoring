#!/usr/bin/env python3
import sys
import os
import json


# getmonitor.py is used to retrieve the monitor values
# using Zabbix system.run[]


def parse_line(name: str, line: str) -> str:
    result_name, result = line.strip().split('=', 1)
    if result_name != name:
        raise Exception(f"Expected '{name}', got '{result_name}'")
    return result


def get(env, command):
    try:
        with open(f'status/{env}.log', 'r') as f:
            time = f.readline().strip()

            test = parse_line('login', f.readline())
            login = parse_line('sbs_login', f.readline())
            pam = parse_line('pam_weblogin', f.readline())
            browser = parse_line('browser', f.readline())
            tries = int(parse_line('tries', f.readline()))

            if command == 'time':
                return time
            elif command == 'test':
                return test
            elif command == 'login':
                return login
            elif command == 'pam':
                return pam
            elif command == 'browser':
                return browser
            elif command == 'json':
                fail_count = (test != "OK") + (login != "OK") + (pam != "OK")
                data = {
                    "time": int(time),
                    "test": test,
                    "login": login,
                    "pam": pam,
                    "tries": tries,
                    "retries": tries - 1,
                    "failure_count": fail_count,
                    "browser": browser
                }
                return json.dumps(data)
    except Exception as e:
        return f"error: {e}\n"


def main():
    if len(sys.argv) < 3:
        sys.exit(sys.argv[0] + "  <env> <command>")
    env = sys.argv[1]
    command = sys.argv[2]

    # find dir of script and chdir to it
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    print(get(env, command))


if __name__ == '__main__':
    main()
