import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://pypi.org/pypi/faiss-cpu/json"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
        print("Latest version:", data["info"]["version"])
        releases = sorted(data["releases"].keys())
        print("Releases:", releases)
        # check files for latest release
        latest_release_files = data["releases"].get(data["info"]["version"], [])
        print(f"\nFiles for {data['info']['version']}:")
        for f in latest_release_files:
            print(f"  Filename: {f['filename']}, Packagetype: {f['packagetype']}, Python: {f['python_version']}")
except Exception as e:
    print("Error:", e)
