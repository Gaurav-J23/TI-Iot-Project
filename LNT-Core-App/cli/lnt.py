import argparse
import os
import sys
import time

import requests

# allow override in case core is not on localhost
API_BASE = os.getenv("LNT_API_BASE", "http://127.0.0.1:8000").rstrip("/")

POLL_INTERVAL = 1.0  # seconds


def _u(path: str) -> str:
    return f"{API_BASE}{path}"


# -------------------- device commands --------------------


def list_devices(args):
    r = requests.get(_u("/device/list"))
    r.raise_for_status()
    print(r.json())


def add_device(args):
    # route expects hostname + ip_address
    r = requests.post(
        _u("/device/add"),
        params={"hostname": args.hostname, "ip_address": args.ip},
    )
    r.raise_for_status()
    print(r.json())


def remove_device(args):
    r = requests.post(_u("/device/remove"), params={"hostname": args.hostname})
    r.raise_for_status()
    print(r.json())


def refresh_host(args):
    r = requests.get(_u(f"/device/refresh/{args.hostname}"))
    r.raise_for_status()
    print(r.json())


def refresh_all(args):
    r = requests.get(_u("/device/refresh-all"))
    r.raise_for_status()
    print(r.json())


def follow_serial(test_id: int, host: str, stream: str):
    print(f"following serial stream {host}/{stream} for test {test_id} (poll {POLL_INTERVAL}s)...")
    last_len = 0

    while True:
        # pull logs+serial
        lr = requests.get(_u(f"/test/{test_id}/logs"))
        if lr.status_code == 404:
            print("test not found")
            sys.exit(1)
        lr.raise_for_status()
        body = lr.json()

        serial_streams = body.get("serial_streams", {})
        host_streams = serial_streams.get(host, {})
        lines = host_streams.get(stream, [])

        # print only new lines
        for line in lines[last_len:]:
            print(line)
        last_len = len(lines)

        # same status logic as follow_test
        sr = requests.get(_u("/test/status"))
        sr.raise_for_status()
        status_body = sr.json()
        tests = status_body.get("tests", {})
        t = tests.get(str(test_id)) or tests.get(test_id)
        status = t.get("status") if isinstance(t, dict) else None

        if status and status not in ("running", "pending"):
            print(f"test {test_id} ended with status: {status}")
            if status == "passed":
                sys.exit(0)
            else:
                sys.exit(1)

        time.sleep(POLL_INTERVAL)


def attach_serial(args):
    follow_serial(args.test_id, args.host, args.stream)



# -------------------- test / job commands --------------------


def start_test(args):
    """
    start a test:

      lnt test start NAME --config /path/to/test.yml --images fw1.bin fw2.bin --follow
    """
    payload = {"name": args.name}

    if args.config:
        payload["config_path"] = args.config

    if args.images:
        payload["image_paths"] = args.images

    r = requests.post(_u("/test/start"), json=payload)
    r.raise_for_status()
    data = r.json()
    print(data)

    test_id = data.get("test_id")
    if args.follow and test_id is not None:
        follow_test(test_id)


def test_status(args):
    r = requests.get(_u("/test/status"))
    r.raise_for_status()
    print(r.json())


def stop_test(args):
    r = requests.post(_u(f"/test/{args.test_id}/stop"))
    r.raise_for_status()
    print(r.json())

def device_test_connection(args):
    r = requests.get(_u("/device/test-connection"))
    r.raise_for_status()
    print(r.json())



def follow_test(test_id: int):
    """
    poll /test/{id}/logs and /test/status
    print new log lines
    exit when status != running/pending (kill signal for jenkins)
    """
    print(f"following test {test_id} (poll {POLL_INTERVAL}s)...")
    last_len = 0

    while True:
        # fetch logs
        lr = requests.get(_u(f"/test/{test_id}/logs"))
        if lr.status_code == 404:
            print("test not found")
            sys.exit(1)
        lr.raise_for_status()
        logs = lr.json().get("logs", [])
        # print only new lines
        for line in logs[last_len:]:
            print(line)
        last_len = len(logs)

        # fetch status snapshot
        sr = requests.get(_u("/test/status"))
        sr.raise_for_status()
        body = sr.json()
        tests = body.get("tests", {})

        # keys may be strings once serialized
        t = tests.get(str(test_id)) or tests.get(test_id)
        status = t.get("status") if isinstance(t, dict) else None

        if status and status not in ("running", "pending"):
            print(f"test {test_id} ended with status: {status}")
            # treat "passed" as success, everything else non-zero
            if status == "passed":
                sys.exit(0)
            else:
                sys.exit(1)

        time.sleep(POLL_INTERVAL)


def attach_logs(args):
    """
    attach to existing test logs:

      lnt test attach 1
    """
    follow_test(args.test_id)


# -------------------- user commands --------------------


def user_login(args):
    r = requests.post(
        _u("/user/login"),
        params={"username": args.username, "password": args.password},
    )
    r.raise_for_status()
    print(r.json())


def list_users(args):
    r = requests.get(_u("/user/list"))
    r.raise_for_status()
    print(r.json())


# -------------------- parser / main --------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lnt", description="LNT CLI for interacting with LNT-Core API"
    )
    sub = parser.add_subparsers(dest="command")

    # device
    dev = sub.add_parser("device", help="device management")
    dev_sub = dev.add_subparsers(dest="action")

    l = dev_sub.add_parser("list", help="list device hosts")
    l.set_defaults(func=list_devices)

    a = dev_sub.add_parser("add", help="add a new device host")
    a.add_argument("hostname", help="hostname label to add")
    a.add_argument("--ip", required=True, help="IP address of device host")
    a.set_defaults(func=add_device)

    rm = dev_sub.add_parser("remove", help="remove a device host")
    rm.add_argument("hostname")
    rm.set_defaults(func=remove_device)

    rf = dev_sub.add_parser("refresh", help="refresh single host status")
    rf.add_argument("hostname")
    rf.set_defaults(func=refresh_host)

    rfa = dev_sub.add_parser("refresh-all", help="refresh all hosts")
    rfa.set_defaults(func=refresh_all)

    tc = dev_sub.add_parser("test-connection", help="test Core -> Host Agent connection")
    tc.set_defaults(func=device_test_connection)

    # test
    test = sub.add_parser("test", help="test/job management")
    test_sub = test.add_subparsers(dest="action")

    st = test_sub.add_parser("start", help="start a test")
    st.add_argument("name", help="test name")
    st.add_argument(
        "--config",
        help="path to test YAML on the core host (or shared filesystem)",
    )
    st.add_argument(
        "--images",
        nargs="*",
        help="firmware image paths (as seen by the core host)",
    )
    st.add_argument(
        "--follow",
        action="store_true",
        help="block and stream logs until test ends",
    )
    st.set_defaults(func=start_test)

    ts = test_sub.add_parser("status", help="show all tests")
    ts.set_defaults(func=test_status)

    sp = test_sub.add_parser("stop", help="stop a running test")
    sp.add_argument("test_id", type=int)
    sp.set_defaults(func=stop_test)

    at = test_sub.add_parser("attach", help="attach to test logs")
    at.add_argument("test_id", type=int)
    at.set_defaults(func=attach_logs)

    aserial = test_sub.add_parser("attach-serial", help="attach to a specific serial stream")
    aserial.add_argument("test_id", type=int)
    aserial.add_argument("--host", required=True, help="host name, e.g. LNT_DEVICE_HOST_1")
    aserial.add_argument("--stream", required=True, help="stream key, e.g. serial_port_x")
    aserial.set_defaults(func=attach_serial)

    # user
    usr = sub.add_parser("user", help="user management")
    usr_sub = usr.add_subparsers(dest="action")

    lg = usr_sub.add_parser("login", help="login user")
    lg.add_argument("username")
    lg.add_argument("password")
    lg.set_defaults(func=user_login)

    lu = usr_sub.add_parser("list", help="list users")
    lu.set_defaults(func=list_users)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return

    try:
        args.func(args)
    except requests.exceptions.RequestException as e:
        print(f"network error talking to core: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
