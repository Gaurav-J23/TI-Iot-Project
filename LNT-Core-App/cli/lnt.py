import argparse, requests, os, json, sys

API_BASE = os.environ.get("LNT_API", "http://127.0.0.1:8000")
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".lnt_token")

def _hdrs():
    if os.path.exists(TOKEN_PATH):
        tok = json.load(open(TOKEN_PATH, "r")).get("access_token")
        if tok:
            return {"Authorization": f"Bearer {tok}"}
    return {}

def _get(path, params=None):
    return requests.get(f"{API_BASE}{path}", params=params, headers=_hdrs(), timeout=10)

def _post(path, json_body=None, params=None):
    return requests.post(f"{API_BASE}{path}", json=json_body, params=params, headers=_hdrs(), timeout=10)

# device
def list_devices(args):
    print(_get("/device/list").json())

def add_device(args):
    print(_post("/device/add", json_body={"hostname": args.hostname}).json())

# test
def start_test(args):
    print(_post("/test/start", json_body={"name": args.name}).json())

def test_status(args):
    print(_get("/test/status").json())

# user
def user_login(args):
    r = requests.post(f"{API_BASE}/user/login", json={"username": args.username, "password": args.password}, timeout=10)
    data = r.json()
    if r.ok and "access_token" in data:
        json.dump(data, open(TOKEN_PATH, "w"))
        print("login ok; token saved")
    else:
        print(data)

def main():
    p = argparse.ArgumentParser(prog="lnt", description="LNT CLI for LNT-Core API")
    p.add_argument("--api", default=API_BASE)
    sub = p.add_subparsers(dest="command")

    dev = sub.add_parser("device"); ds = dev.add_subparsers(dest="action")
    ds.add_parser("list").set_defaults(func=list_devices)
    a = ds.add_parser("add"); a.add_argument("hostname"); a.set_defaults(func=add_device)

    tst = sub.add_parser("test"); ts = tst.add_subparsers(dest="action")
    s = ts.add_parser("start"); s.add_argument("name"); s.set_defaults(func=start_test)
    ts.add_parser("status").set_defaults(func=test_status)

    usr = sub.add_parser("user"); us = usr.add_subparsers(dest="action")
    lg = us.add_parser("login"); lg.add_argument("username"); lg.add_argument("password"); lg.set_defaults(func=user_login)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
