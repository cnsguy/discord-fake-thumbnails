import urllib.request
import urllib.parse
import PIL.Image
import io
import socket

def get(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0";
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
    return urllib.request.urlopen(req)

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

        if "link" not in query:
            request.send_code(403)
            return

        link = query["link"][0]

        print("nsfw-bypass: agent:", agent)
        print("nsfw-bypass: link:", link)

        if should_be_filtered(link):
            request.send_code(403)
            return

        with get(link) as result:
            type = result.info().get_content_type()

            if not type.startswith("image/"):
                request.send_code(403)
                return

            image_bytes = result.read()

            if "discordbot" in agent.lower():
                info = PIL.Image.open(io.BytesIO(image_bytes))
                print("nsfw-bypass: discordbot detected, spoofing %dx%d thumbnail" % info.size)
                spoofed = PIL.Image.new('RGBA', info.size, (255, 255, 255, 0))
                spoofed_bytes = io.BytesIO()
                spoofed.save(spoofed_bytes, format='PNG')
                spoofed_bytes = spoofed_bytes.getvalue()
                request.send_response(200)
                request.send_header("Content-type", "image/png")
                request.send_header('Cache-Control', 'no-store, must-revalidate')
                request.send_header('Expires', '0')
                request.end_headers()
                request.wfile.write(spoofed_bytes)
                return

            request.send_response(200)
            request.send_header("Content-type", result.info().get_content_type())
            request.send_header('Cache-Control', 'no-store, must-revalidate')
            request.send_header('Expires', '0')
            request.end_headers()
            request.wfile.write(image_bytes)

    except Exception:
        request.send_code(403)
        return