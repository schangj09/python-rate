# Python 3 server for simple token counting rate limiter

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from rate_component import RateComponent
import time

hostName = "localhost"
serverPort = 8080

## Class: RateComponentServer
## Http request handler for the server which provides rate limiter functionality.
class RateComponentServer(BaseHTTPRequestHandler):
    component = RateComponent()

    ## Method: do_GET
    ## Path: "/take"
    ## Params: "route" -> route name to check
    ## Returns a result indicating if the route request should be accepted or rejected and 
    ## how many tokens are remaining. Returns 400 for unknown route param.
    def do_GET(self):
        url = urlparse(self.path)
        query = url.query
        qs = parse_qs(query)

        if (qs["route"] and len(qs["route"]) > 0):
            r = qs["route"][0]
            result = self.component.take(r)

        if result:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes(f"<code>{result}</code>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<code>Failed - BAD REQUEST</code>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = ThreadingHTTPServer((hostName, serverPort), RateComponentServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")