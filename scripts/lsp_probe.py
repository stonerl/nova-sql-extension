#!/usr/bin/env python3
"""Scripted LSP session against the bundled sqls binary. Bypasses Nova.

Usage: python3 lsp_probe.py <path-to-sqls-binary> [sqlfile]
Prints the raw JSON responses of interest: initialize capabilities (hover),
and the textDocument/hover response for the cursor position given below.
"""

import json
import subprocess
import sys
import threading

BINARY = None
SQL_TEXT = "SELECT 1 FROM t"
HOVER_LINE = 0
HOVER_CHAR = 1  # cursor inside 'SELECT'


def frame(msg: dict) -> bytes:
    body = json.dumps(msg).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode() + body


def reader(proc, sink):
    buf = b""
    while True:
        chunk = proc.stdout.read(1)
        if not chunk:
            break
        buf += chunk
        while b"\r\n\r\n" in buf:
            head, rest = buf.split(b"\r\n\r\n", 1)
            length = int([l for l in head.split(b"\r\n") if l.lower().startswith(b"content-length")][0].split(b":")[1])
            while len(rest) < length:
                rest += proc.stdout.read(length - len(rest))
            body, buf = rest[:length], rest[length:]
            sink.append(json.loads(body.decode("utf-8")))


def main():
    import sys
    global BINARY, SQL_TEXT, HOVER_CHAR
    BINARY = sys.argv[1]
    LANG_ID = "sql"
    if len(sys.argv) > 2:
        SQL_TEXT = open(sys.argv[2], "rb").read().decode("utf-8")
    if len(sys.argv) > 3:
        LANG_ID = sys.argv[3]
    if len(sys.argv) > 4:
        HOVER_CHAR = int(sys.argv[4])

    proc = subprocess.Popen(
        [BINARY],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    sink = []
    t = threading.Thread(target=reader, args=(proc, sink), daemon=True)
    t.start()

    def send(msg):
        proc.stdin.write(frame(msg))
        proc.stdin.flush()

    def wait_for(predicate, tries=100):
        for _ in range(tries):
            for m in sink:
                if predicate(m):
                    return m
            import time
            time.sleep(0.05)
        return None

    rid = 0
    def call(method, params):
        nonlocal rid
        rid += 1
        send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        return wait_for(lambda m: m.get("id") == rid and ("result" in m or "error" in m))

    init = call("initialize", {
        "processId": None,
        "rootUri": "file:///tmp",
        "capabilities": {},
    })
    caps = (init or {}).get("result", {}).get("capabilities", {})
    print("hoverProvider advertised:", caps.get("hoverProvider"))
    send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
    import time
    time.sleep(0.5)

    popup = [m for m in sink if m.get("method") == "window/showMessage"
             and "no database connection" in json.dumps(m)]
    print("no-db showMessage notifications received:", len(popup))

    uri = "file:///tmp/hover_test.sql"
    send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {"uri": uri, "languageId": LANG_ID, "version": 1, "text": SQL_TEXT},
        },
    })
    import time
    time.sleep(0.3)

    for ch in range(min(HOVER_CHAR + 3, len(SQL_TEXT))):
        rid += 1
        send({
            "jsonrpc": "2.0",
            "id": rid,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": HOVER_LINE, "character": ch},
            },
        })
        resp = wait_for(lambda m: m.get("id") == rid and ("result" in m or "error" in m))
        label = SQL_TEXT[ch]
        if resp is None:
            print(f"char {ch} ({label!r}): NO RESPONSE")
        elif "error" in resp:
            print(f"char {ch} ({label!r}): ERROR {json.dumps(resp['error'])[:200]}")
        else:
            r = resp["result"]
            if r and r.get("contents"):
                c = r["contents"]
                val = c.get("value", "") if isinstance(c, dict) else str(c)
                footer = ""
                for line in val.split("\n"):
                    if line.startswith("Docs:"):
                        footer = line
                print(f"char {ch} ({label!r}): HOVER ✓  ({len(val)} chars) footer={footer!r}")
            else:
                print(f"char {ch} ({label!r}): null hover")

    proc.terminate()


if __name__ == "__main__":
    main()
