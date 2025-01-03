from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# Change to the directory containing your web files
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create server
handler = SimpleHTTPRequestHandler
httpd = HTTPServer(('localhost', 8000), handler)

print("Server started at http://localhost:8000")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.") 