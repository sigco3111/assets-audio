import json, re, subprocess, urllib.request, traceback

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
INDEX = "https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
OUT = []
NAMES = ["512 Sound Effects (8-bit style)", "RPG Sound Pack", "Castle Kit", "Mini Arena", "Graveyard Kit",
         "Survival Kit", "Retro Urban Kit", "Holiday Kit", "Space Kit"]

def log(s):
    print(s, flush=True)
    OUT.append(str(s))

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def main():
    try:
        raw = get(INDEX)
        log("index bytes " + str(len(raw)))
        j = json.loads(raw)
        names = set()
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "name" and isinstance(v, str):
                        names.add(v)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(j)
        log("names " + str(len(names)))
        nset = set(norm(n) for n in names)
        for n in NAMES:
            log("DUPCHECK " + n + " -> " + str(norm(n) in nset))
        try:
            html = get("https://opengameart.org/content/512-sound-effects-8-bit-style")
            log("oga bytes " + str(len(html)) + " cc0 " + str("CC0" in html))
            z = re.findall(r'https://opengameart\.org/sites/default/files/[^"\'<> ]+\.zip', html)
            log("oga zips " + json.dumps(z[:5]))
        except Exception as e:
            log("oga error " + repr(e))
        try:
            k = get("https://kenney.nl/assets/castle-kit")
            log("kenney bytes " + str(len(k)) + " cc0 " + str("CC0" in k))
            z2 = [h for h in re.findall(r'href="([^"]+?\.zip)"', k) if "/media/pages/assets/" in h]
            log("kenney zips " + json.dumps(z2[:3]))
        except Exception as e:
            log("kenney error " + repr(e))
    except Exception:
        log("FATAL " + traceback.format_exc())
    open("tools/a101b_diag.txt", "w", encoding="utf-8").write("\n".join(OUT) + "\n")
    subprocess.run('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" add tools/a101b_diag.txt && git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "진단: A101b 진단 결과" && git push origin HEAD:main', shell=True)

main()
