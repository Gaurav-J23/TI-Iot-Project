import argparse, requests, os, json, sys

API_BASE = os.environ.get("LNT_API", "http://127.0.0.1:8000")
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".lnt_token")

def _hdrs():
    if os.path.exists(TOKEN_PATH):
        try:
            tok = json.load(open(TOKEN_PATH, "r")).get("access_token")
            if tok:
                return {"Authorization": f"Bearer {tok}"}
        except Exception:
            pass
    return {}

def _get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, headers=_hdrs(), timeout=10)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

def _post(path, json_body=None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=json_body, headers=_hdrs(), timeout=30)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"error: {e}")
        try:
            print(r.text)
        except Exception:
            pass
        sys.exit(1)

def _delete(path):
    try:
        r = requests.delete(f"{API_BASE}{path}", headers=_hdrs(), timeout=10)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

# --- DEVICE COMMANDS ---

def list_devices(args):
    print(json.dumps(_get("/device").json(), indent=2))

def add_device(args):
    body = {"hostname": args.hostname, "ip": args.ip}
    print(json.dumps(_post("/device", json_body=body).json(), indent=2))

def remove_device(args):
    print(json.dumps(_delete(f"/device/{args.hostname}").json(), indent=2))

def refresh_device(args):
    print(json.dumps(_post(f"/device/{args.hostname}/refresh").json(), indent=2))

# --- TEST COMMANDS ---

def start_test(args):
    body = {
        "name": args.name,
        "config_path": args.config,
        "image_paths": args.image or [],
    }
    print(json.dumps(_post("/test/start", json_body=body).json(), indent=2))

def stop_test(args):
    print(json.dumps(_post(f"/test/{args.id}/stop").json(), indent=2))

def test_status(args):
    print(json.dumps(_get("/test/status").json(), indent=2))

def test_logs(args):
    print(json.dumps(_get(f"/test/{args.id}/logs").json(), indent=2))

# --- USER COMMANDS ---

def user_login(args):
    r = requests.post(
        f"{API_BASE}/user/login",
        json={"username": args.username, "password": args.password},
        timeout=10,
    )
    data = r.json()
    if r.ok and "access_token" in data:
        with open(TOKEN_PATH, "w") as f:
            json.dump(data, f)
        print(f"login successful. token saved to {TOKEN_PATH}")
    else:
        print(f"login failed: {data}")

def user_list(args):
    print(json.dumps(_get("/user/list").json(), indent=2))

def user_add(args):
    body = {
        "username": args.new_username,
        "password": args.new_password,
        "role": args.role,
    }
    print(json.dumps(_post("/user/add", json_body=body).json(), indent=2))

def user_rm(args):
    print(json.dumps(_delete(f"/user/{args.rm_username}").json(), indent=2))

# --- MAIN ---

def main():
    p = argparse.ArgumentParser(prog="lnt", description="LNT CLI for LNT-Core API")
    p.add_argument("--api", default=API_BASE, help="override api url")
    sub = p.add_subparsers(dest="command")

    # DEVICE
    dev = sub.add_parser("device", help="manage device hosts")
    ds = dev.add_subparsers(dest="action")

    d_list = ds.add_parser("list")
    d_list.set_defaults(func=list_devices)

    d_add = ds.add_parser("add")
    d_add.add_argument("hostname")
    d_add.add_argument("ip")
    d_add.set_defaults(func=add_device)

    d_rm = ds.add_parser("rm")
    d_rm.add_argument("hostname")
    d_rm.set_defaults(func=remove_device)

    d_ref = ds.add_parser("refresh")
    d_ref.add_argument("hostname")
    d_ref.set_defaults(func=refresh_device)

    # TEST
    tst = sub.add_parser("test", help="manage tests")
    ts = tst.add_subparsers(dest="action")

    t_start = ts.add_parser("start")
    t_start.add_argument("name", help="name of the test job")
    t_start.add_argument("--config", required=True, help="path to test.yaml")
    t_start.add_argument(
        "--image",
        action="append",
        help="path to firmware image (can use multiple times)",
    )
    t_start.set_defaults(func=start_test)

    t_status = ts.add_parser("status")
    t_status.set_defaults(func=test_status)

    t_stop = ts.add_parser("stop")
    t_stop.add_argument("id", type=int, help="test id to stop")
    t_stop.set_defaults(func=stop_test)

    t_logs = ts.add_parser("logs")
    t_logs.add_argument("id", type=int, help="test id to view logs")
    t_logs.set_defaults(func=test_logs)

    # USER
    usr = sub.add_parser("user", help="manage users")
    us = usr.add_subparsers(dest="action")

    u_login = us.add_parser("login")
    u_login.add_argument("username")
    u_login.add_argument("password")
    u_login.set_defaults(func=user_login)

    u_list = us.add_parser("list")
    u_list.set_defaults(func=user_list)

    u_add = us.add_parser("add")
    u_add.add_argument("new_username")
    u_add.add_argument("new_password")
    u_add.add_argument("--role", default="user")
    u_add.set_defaults(func=user_add)

    u_rm = us.add_parser("rm")
    u_rm.add_argument("rm_username")
    u_rm.set_defaults(func=user_rm)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
