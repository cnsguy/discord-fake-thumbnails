import http.server
import mimetypes
import os.path
import os
import random
import glob
import urllib.parse
import sys


def choose_file(path):
    candidates = []

    for fname in os.listdir(path):
        fname = os.path.join(path, fname)

        if not os.path.isfile(fname):
            continue

        candidates.append(fname)

    if len(candidates) == 0:
        return None

    return random.choice(candidates)


def get_scripts():
    path = os.path.join("scripts", "*.py")
    files = glob.glob(path)
    files = [file.split(os.path.sep)[1] for file in files]
    files = [file.split(".")[0] for file in files]
    return files


class HookedHTTPHandler(http.server.BaseHTTPRequestHandler):
    def send_code(self, code):
        self.send_response(code)
        self.send_header("Content-type", "text/plain;charset=UTF-8")
        self.end_headers()
        self.wfile.write(b"%d." % code)

    def send_404(self):
        self.send_code(404)

    def send_file(self, fpath):
        (mime_type, _) = mimetypes.guess_type(fpath)

        if mime_type == None:
            self.send_404()
            return

        self.send_response(200)
        self.send_header("Content-type", mime_type)
        self.end_headers()

        with open(fpath, "rb") as f:
            content = f.read()
            self.wfile.write(content)

    def send_dir(self, path):
        fpath = choose_file(path)

        if fpath == None:
            self.send_404()
            return

        self.send_file(fpath)

    def send_script(self, parsed):
        full_path = "scripts.%s" % parsed.path

        if full_path in sys.modules:
            del sys.modules[full_path]

        __import__(full_path)
        data = sys.modules[full_path]
        main = getattr(data, "main")
        query = urllib.parse.parse_qs(parsed.query)
        main(self, query)

    def do_GET(self):
        if ".." in self.path:
            self.send_404()
            return

        path = self.path.replace("\\", "/")

        if not path.startswith("/"):
            self.send_404()
            return

        path = path[1:]
        parsed = urllib.parse.urlparse(path)
        scripts = get_scripts()

        if parsed.path in scripts:
            self.send_script(parsed)
            return

        base = os.path.normpath(os.path.join(os.getcwd(), "files"))
        path = os.path.normpath(os.path.join(base, *path.split("/")))
        common = os.path.commonpath([base, path])

        """
        print("==req==")
        print(self.path)
        print(self.headers)
        print(path, base, path == base)
        print("==req end==")
        """

        if common != base:
            self.send_404()
            return

        if path == base:
            self.send_file(os.path.join(base, "index.html"))
            return

        elif os.path.isfile(path):
            self.send_file(path)
        elif os.path.isdir(path):
            self.send_dir(path)
        else:
            self.send_404()


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: %s <bindip> <port>\n" % sys.argv[0])
        sys.exit()

    ip = sys.argv[1]
    port = int(sys.argv[2])
    server = http.server.HTTPServer((ip, port), HookedHTTPHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


main()
