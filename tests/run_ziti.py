#  Copyright (c) 2022.  NetFoundry, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#!/usr/bin/env python3
import json, os, time, subprocess, platform, shutil, stat, sys, tarfile, tempfile, urllib.request as url

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "openziti")
GITHUB_REPO_NAME  = os.getenv("GITHUB_REPO_NAME",  "ziti")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN", "")

def _arch():
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):         return "amd64"
    if m in ("aarch64", "arm64"):        return "arm64"
    if m.startswith("arm"):              return "arm"
    raise RuntimeError(f"unsupported arch: {m}")

def _os():
    p = sys.platform
    if   p.startswith("linux"):   return "linux"
    elif p == "darwin":           return "darwin"
    elif p in ("win32", "cygwin"):return "windows"
    raise RuntimeError(f"unsupported os: {p}")

def _github_json(path):
    req = url.Request(f"https://api.github.com{path}")
    if GITHUB_TOKEN: req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with url.urlopen(req) as r:
        return json.load(r)

def _latest_version():
    data = _github_json(f"/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest")
    return data["tag_name"], next(a["name"] for a in data["assets"]
                                  if a["name"].startswith(f"ziti-{_os()}-{_arch()}-"))

def _verify_version(vtag):
    try:
        data = _github_json(f"/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/tags/{vtag}")
        fname = next(a["name"] for a in data["assets"]
                     if a["name"].startswith(f"ziti-{_os()}-{_arch()}-"))
        return vtag, fname
    except Exception as e:
        raise RuntimeError(f"version {vtag} not found") from e

def get_ziti(add_to_path: bool = False) -> str:
    """Download & extract ziti; return path to binary, with progress output."""
    override = os.getenv("ZITI_VERSION_OVERRIDE")
    tag, archive = (_verify_version(override) if override else _latest_version())
    print(f"🔍 using tag={tag}  archive={archive}")

    zhome = os.getenv("ZITI_HOME", os.path.expanduser("~/.ziti"))
    zbin = os.getenv("ZITI_BIN_DIR", os.path.join(zhome, "ziti-bin", f"ziti-{tag}"))
    ziti_path = os.path.join(zbin, "ziti.exe" if sys.platform == "win32" else "ziti")

    if os.path.isfile(ziti_path):
        print(f"✅ existing ziti at {ziti_path}")
        if add_to_path and zbin not in os.getenv("PATH", ""):
            os.environ["PATH"] += os.pathsep + zbin
            print(f"➕ added {zbin} to PATH")
        return ziti_path

    print(f"📁 creating {zbin}")
    os.makedirs(zbin, exist_ok=True)

    url_file = (
        f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
        f"/releases/download/{tag}/{archive}"
    )
    print(f"⬇️  downloading {url_file}")
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        with url.urlopen(url_file) as r, open(tmp.name, "wb") as f:
            shutil.copyfileobj(r, f)
        print("✔️  download complete")

        print("📦 extracting …")
        if sys.platform == "win32":
            import zipfile
            with zipfile.ZipFile(tmp.name) as z:
                z.extractall(zbin)
        else:
            with tarfile.open(tmp.name) as t:
                member = next(m for m in t.getmembers()
                              if m.name.endswith("/ziti") or m.name == "ziti")
                t.extract(member, path=zbin if member.name == "ziti"
                          else os.path.join(zbin, "tmp"))
                if "/" in member.name:
                    shutil.move(os.path.join(zbin, "tmp", member.name), ziti_path)
                    shutil.rmtree(os.path.join(zbin, "tmp"))
        os.chmod(ziti_path, os.stat(ziti_path).st_mode | stat.S_IEXEC)
        print(f"✅ extracted to {ziti_path}")

        if add_to_path:
            os.environ["PATH"] += os.pathsep + zbin
            print(f"➕ added {zbin} to PATH")

        return ziti_path
    finally:
        try:
            os.unlink(tmp.name)
        except PermissionError:
            pass

def start_ziti_quickstart(ziti_path: str, home: str | None = None, log_file: str = "quickstart.log") -> subprocess.Popen:
    print("💥 starting ziti quickstart...", flush=True)
    cmd = [ziti_path, "edge", "quickstart", "--ctrl-address", "127.0.0.1", "--router-address", "127.0.0.1"]
    if home:
        cmd += ["--home", home]
    log = open(log_file, "w")
    return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)

def wait_for_controller(host: str = "127.0.0.1", port: int = 1280, timeout: int = 60) -> None:
    import time, ssl, http.client
    ctx = ssl._create_unverified_context()
    end = time.time() + timeout
    while time.time() < end:
        try:
            conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=1)
            conn.request("GET", "/edge/client/v1/version")
            if conn.getresponse().status == 200:
                conn.close()
                return
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"timeout waiting for https://{host}:{port}")

def run(cmd):
    print(f"📟 running: {cmd}", flush=True)
    try:
        result = subprocess.run(cmd, shell=True, check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Command failed")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        raise

def login(ziti):
    run(f"{ziti} edge login 127.0.0.1:1280 -u admin -p admin -y")

def create_and_enroll_identities(ziti):
    run(rf"{ziti} edge create identity pytest -o pytest.jwt")
    run(rf"{ziti} edge enroll ./pytest.jwt")
    run(rf"{ziti} edge create identity flasksvr -o flasksvr.jwt")
    run(rf"{ziti} edge enroll ./flasksvr.jwt")

def create_service(ziti):
    run(rf"{ziti} edge create service httpbin.ziti")
    run(rf"{ziti} edge create service-policy httpbin.ziti-bind Bind --service-roles \"@httpbin.ziti\" --identity-roles \"@flasksvr\"")
    run(rf"{ziti} edge create service-policy httpbin.ziti-dial Dial --service-roles \"@httpbin.ziti\" --identity-roles \"@pytest\"")

def wait_for_terminator(ziti, timeout=20):
    for i in range(timeout):
        out = subprocess.check_output(f"{ziti} edge list terminators", shell=True).decode()
        if 'httpbin.ziti' in out:
            print("✅ terminator found", flush=True)
            return
        print("🕒 waiting for terminator", flush=True)
        time.sleep(1)
    raise TimeoutError("Timed out waiting for terminator")

def start_flask_app():
    proc = subprocess.Popen([
        sys.executable, "sample/flask-of-ziti/helloFlazk.py", "flasksvr.json", "httpbin.ziti"
    ])
    print("🚀 flask app started", flush=True)
    time.sleep(2) # waits for terminators to be created
    return proc
