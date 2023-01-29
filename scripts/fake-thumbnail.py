import urllib.request
import os.path
import urllib.parse
import socket
import os
import csv
import ipaddress


def get(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0"
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
    return urllib.request.urlopen(req)


def get_asn(ip):
    if not os.path.exists("ip-asn.csv"):
        return None

    ip = ipaddress.IPv4Address(ip)

    with open("ip-asn.csv", "r") as f:
        reader = csv.reader(f)
        i = 0

        for batch in reader:
            if i > 0:
                netw = ipaddress.IPv4Network(batch[0])

                if ip in netw:
                    return batch[2]

            i += 1

    return None


def should_be_filtered(link):
    bad = ["localhost", "127.0.0.1"]
    parsed = urllib.parse.urlparse(link)

    if parsed.path in bad:
        return True

    if parsed.path.startswith(socket.gethostname()):
        return True

    if parsed.scheme != "http" and parsed.scheme != "https":
        return True

    return False


def main(request, query):
    try:
        if "User-Agent" not in request.headers:
            request.send_code(403)
            return

        agent = request.headers["User-Agent"]

        if "thumb" not in query or "actual" not in query:
            request.send_code(403)
            return

        thumb = query["thumb"][0]
        actual = query["actual"][0]
        ip = request.client_address[0]
        asn = get_asn(ip)

        print("fake-thumbnail: agent:", agent)
        print("fake-thumbnail: ip:", ip)
        print("fake-thumbnail: asn:", asn)
        print("fake-thumbnail: thumb:", thumb)
        print("fake-thumbnail: actual:", actual)

        if should_be_filtered(thumb) or should_be_filtered(actual):
            request.send_code(403)
            return

        if "discordbot" in agent.lower() or asn is not None and "google" in asn.lower():
            print("fake-thumbnail: faking.")
            target = thumb
        else:
            target = actual

        with get(target) as result:
            type = result.info().get_content_type()

            if not type.startswith("image/"):
                request.send_code(403)
                return

            image_bytes = result.read()
            request.send_response(200)
            request.send_header("Content-type", type)
            request.end_headers()
            request.wfile.write(image_bytes)
    except Exception:
        request.send_code(403)
        return
