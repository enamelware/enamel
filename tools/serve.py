"""Serve the repo over http on 127.0.0.1 and open the style guide.

Firefox here is sandboxed and can't read ../tokens/enamel.css from a file://
page, so the docs must be viewed over http. Binds to 127.0.0.1 only, on a
free port, and opens /docs/overview.html (or /docs/index.html if there is no
overview yet) in the default browser. Stops on Ctrl+C or when its terminal
window is closed. Standard library only.

    python3 tools/serve.py            # serve and open the browser
    python3 tools/serve.py --no-open  # serve only, print the URL
"""
import functools, http.server, os, signal, sys, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        # Don't serve hidden files or folders such as .git.
        parts = self.path.split("?", 1)[0].split("/")
        if any(p.startswith(".") and p not in (".", "..") for p in parts):
            self.send_error(404)
            return None
        return super().send_head()


def start_page():
    for name in ("overview.html", "index.html"):
        if os.path.exists(os.path.join(ROOT, "docs", name)):
            return f"/docs/{name}"
    sys.exit("no docs/overview.html or docs/index.html to open")


def main():
    page = start_page()
    handler = functools.partial(Handler, directory=ROOT)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    url = f"http://127.0.0.1:{server.server_port}{page}"

    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGHUP, stop)   # terminal window closed
    signal.signal(signal.SIGTERM, stop)

    print(f"Enamel style guide: {url}", flush=True)
    print("Close this window (or press Ctrl+C) to stop the server.", flush=True)
    if "--no-open" not in sys.argv[1:]:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Server stopped.", flush=True)


if __name__ == "__main__":
    main()
