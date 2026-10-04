#!/usr/bin/env python3
"""Scripted LSP session against the bundled sqls binary. Bypasses Nova.

Usage: python3 lsp_probe.py <path-to-sqls-binary> [sqlfile]
       python3 lsp_probe.py <path-to-sqls-binary> --completions
Prints the raw JSON responses of interest: initialize capabilities (hover),
and the textDocument/hover response for the cursor position given below.
The --completions mode asserts dialect-correct keyword completions for a
matrix of languageIds (no database connection configured).
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


class Session:
    def __init__(self):
        self.proc = subprocess.Popen(
            [BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.sink = []
        self.rid = 0
        t = threading.Thread(target=reader, args=(self.proc, self.sink), daemon=True)
        t.start()

    def send(self, msg):
        self.proc.stdin.write(frame(msg))
        self.proc.stdin.flush()

    def wait_for(self, predicate, tries=100):
        import time
        for _ in range(tries):
            for m in self.sink:
                if predicate(m):
                    return m
            time.sleep(0.05)
        return None

    def call(self, method, params):
        self.rid += 1
        self.send({"jsonrpc": "2.0", "id": self.rid, "method": method, "params": params})
        return self.wait_for(lambda m: m.get("id") == self.rid and ("result" in m or "error" in m))


def completion_probe():
    import time

    cases = [
        # (languageId, text, cursor char, must-contain label, must-not-contain)
        ("mysql", "USE ", 4, "STRAIGHT_JOIN", "ARRAY_AGG"),
        ("postgresql", "USE ", 4, "ANALYSE", None),
        ("tsql", "USE ", 4, "PIVOT", "ANALYSE"),
        ("sqlite", "USE ", 4, "PRAGMA", "ANALYSE"),
        ("plsql", "USE ", 4, "NOCOMPRESS", None),
        ("snowflake", "USE ", 4, "ALLOCATE", "RLIKE"),
        ("sql-generic", "USE ", 4, "ALLOCATE", "RLIKE"),
    ]
    failures = 0
    for lang, text, char, must, must_not in cases:
        s = Session()
        s.call("initialize", {"processId": None, "rootUri": "file:///tmp", "capabilities": {}})
        s.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        time.sleep(0.3)
        s.call("textDocument/didOpen", {
            "textDocument": {"uri": "file:///tmp/probe.sql", "languageId": lang, "version": 1, "text": text},
        })
        time.sleep(0.3)
        r = s.call("textDocument/completion", {
            "textDocument": {"uri": "file:///tmp/probe.sql"},
            "position": {"line": 0, "character": char},
        })
        s.proc.terminate()
        items = (r or {}).get("result")
        if isinstance(items, dict):
            items = items.get("items")
        labels = {i.get("label", "") for i in (items or [])}
        ok = must in labels and (must_not is None or must_not not in labels)
        print(f"{lang:12s} items={len(labels):4d} has {must}: {must in labels}"
              + (f" wrongly has {must_not}: {must_not in labels}" if must_not else "")
              + ("" if ok else "  << FAIL"))
        if not ok:
            failures += 1
    print("completion probe:", "PASS" if failures == 0 else f"{failures} FAILURES")
    sys.exit(0 if failures == 0 else 1)


def main():
    import sys
    global BINARY, SQL_TEXT, HOVER_CHAR
    BINARY = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--completions":
        completion_probe()
        return
    LANG_ID = "sql"
    if len(sys.argv) > 2:
        SQL_TEXT = open(sys.argv[2], "rb").read().decode("utf-8")
    if len(sys.argv) > 3:
        LANG_ID = sys.argv[3]
    if len(sys.argv) > 4:
        HOVER_CHAR = int(sys.argv[4])

    proc = Session()

    init = proc.call("initialize", {
        "processId": None,
        "rootUri": "file:///tmp",
        "capabilities": {},
    })
    caps = (init or {}).get("result", {}).get("capabilities", {})
    print("hoverProvider advertised:", caps.get("hoverProvider"))
    proc.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
    import time
    time.sleep(0.5)

    popup = [m for m in proc.sink if m.get("method") == "window/showMessage"
             and "no database connection" in json.dumps(m)]
    print("no-db showMessage notifications received:", len(popup))

    uri = "file:///tmp/hover_test.sql"
    proc.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {"uri": uri, "languageId": LANG_ID, "version": 1, "text": SQL_TEXT},
        },
    })
    import time
    time.sleep(0.3)

    for ch in range(min(HOVER_CHAR + 3, len(SQL_TEXT))):
        proc.rid += 1
        proc.send({
            "jsonrpc": "2.0",
            "id": proc.rid,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": HOVER_LINE, "character": ch},
            },
        })
        resp = proc.wait_for(lambda m: m.get("id") == proc.rid and ("result" in m or "error" in m))
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
