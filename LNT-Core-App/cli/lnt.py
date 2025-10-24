import argparse
import requests
import sys

API_BASE = "http://127.0.0.1:8000"

def list_devices(args):
    r = requests.get(f"{API_BASE}/device/list")
    print(r.json())

def add_device(args):
    r = requests.post(f"{API_BASE}/device/add", params={"hostname": args.hostname})
    print(r.json())

def start_test(args):
    r = requests.post(f"{API_BASE}/test/start", params={"test_name": args.name})
    print(r.json())

def test_status(args):
    r = requests.get(f"{API_BASE}/test/status")
    print(r.json())

def user_login(args):
    r = requests.post(f"{API_BASE}/user/login", params={"username": args.username, "password": args.password})
    print(r.json())

def list_users(args):
    r = requests.get(f"{API_BASE}/user/list")
    print(r.json())

def main():
    parser = argparse.ArgumentParser(prog="lnt", description="LNT CLI for interacting with LNT-Core API")
    sub = parser.add_subparsers(dest="command")

    # device commands
    dev = sub.add_parser("device", help="device management")
    dev_sub = dev.add_subparsers(dest="action")

    l = dev_sub.add_parser("list", help="list connected devices")
    l.set_defaults(func=list_devices)

    a = dev_sub.add_parser("add", help="add a new device host")
    a.add_argument("hostname", help="hostname to add")
    a.set_defaults(func=add_device)

    # test commands
    test = sub.add_parser("test", help="test management")
    test_sub = test.add_subparsers(dest="action")
    s = test_sub.add_parser("start", help="start a test")
    s.add_argument("name", help="test name")
    s.set_defaults(func=start_test)

    g = test_sub.add_parser("status", help="get test status")
    g.set_defaults(func=test_status)



    # user commands
    usr = sub.add_parser("user", help="user management")
    usr_sub = usr.add_subparsers(dest="action")

    lg = usr_sub.add_parser("login", help="login user")
    lg.add_argument("username")
    lg.add_argument("password")
    lg.set_defaults(func=user_login)

    lu = usr_sub.add_parser("list", help="list users")
    lu.set_defaults(func=list_users)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()



if __name__ == "__main__":
    main()
