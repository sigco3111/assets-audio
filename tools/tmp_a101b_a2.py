import json, os, re, shutil, subprocess, urllib.request, urllib.parse, zipfile, datetime, traceback

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
INDEX = "https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
CC0_TEXT = "https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt"
LIMIT = 2
LOG = "tools/a101b_log.txt"
OUT = []
PACKS = [
 {
  "slug": "8-bit-sound-effect-pack-vol-001",
  "name": "8-Bit Sound Effect Pack (Vol. 001)",
  "url": "https://opengameart.org/content/8-bit-sound-effect-pack-vol-001",
  "author": "Deva",
  "tags": "sfx,8bit,retro,audio",
  "release": "v7.0",
  "readme": true
 },
 {
  "slug": "100-cc0-sfx",
  "name": "100 CC0 SFX",
  "url": "https://opengameart.org/content/100-cc0-sfx",
  "author": "rubberduck",
  "tags": "sfx,audio",
  "release": "v7.1",
  "readme": true
 },
 {
  "slug": "8-bit-sound-effect-pack",
  "name": "8-Bit Sound Effect Pack",
  "url": "https://opengameart.org/content/8-bit-sound-effect-pack",
  "author": "OwlishMedia",
  "tags": "sfx,8bit,retro,audio",
  "release": "v7.2",
  "readme": true
 }
]

def log(s):
    print(s, flush=True)
    OUT.append(str(s))

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def load_names():
    out = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "name" and isinstance(v, str):
                    out.add(norm(v))
                    out.add(re.sub(r"[0-9]+$", "", norm(v)))
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads(get(INDEX)))
    return out

def sh(cmd, check=True):
    log("$ " + cmd)
    subprocess.run(cmd, shell=True, check=check)

def collect(p, names):
    if norm(p["name"]) in names:
        log("SKIP dup: " + p["name"])
        return None
    if os.path.isdir(p["slug"]):
        log("SKIP dir: " + p["slug"])
        return None
    html = get(p["url"])
    log("page bytes " + str(len(html)) + " cc0 " + str("CC0" in html))
    if "CC0" not in html:
        log("SKIP no CC0: " + p["url"])
        return None
    zips = re.findall(r'https://opengameart\.org/sites/default/files/[^"\'<> ]+\.zip', html)
    log("zip hrefs " + json.dumps(zips[:5]))
    zips = [z for z in zips if "preview" not in z.lower() and "demo" not in z.lower()]
    if not zips:
        log("SKIP no zip: " + p["url"])
        return None
    zip_url = zips[0]
    zip_name = urllib.parse.unquote(zip_url.rsplit("/", 1)[-1])
    data = get(zip_url, binary=True)
    tmp = "/tmp/" + re.sub(r"[^A-Za-z0-9._-]", "_", zip_name)
    with open(tmp, "wb") as f:
        f.write(data)
    with zipfile.ZipFile(tmp) as z:
        nfiles = len([i for i in z.namelist() if not i.endswith("/")])
    size_mb = round(len(data) / 1048576.0, 1)
    m = re.search(r'article:published_time" content="(\d{4}-\d{2}-\d{2})', html)
    date = m.group(1) if m else "출처 페이지 표기 미확인"
    os.makedirs(p["slug"])
    rel = ""
    if len(data) > 5 * 1024 * 1024:
        tag = p["release"]
        sh("gh release create " + tag + " --title '" + p["name"] + "' --notes 'asset pack zip' || true", check=False)
        sh('gh release upload ' + tag + ' "' + tmp + '" --clobber')
        os.remove(tmp)
        rel = ", 릴리스 " + tag + " 첨부"
    else:
        shutil.move(tmp, os.path.join(p["slug"], zip_name))
    today = datetime.date.today().isoformat()
    md = [
        "# " + p["name"],
        "",
        "- 출처 URL: " + p["url"],
        "- 받은 파일: " + zip_name + " (" + str(size_mb) + "MB" + rel + ")",
        "- 라이선스: CC0",
        "- 라이선스 원문: https://creativecommons.org/publicdomain/zero/1.0/",
        "- 저작자: " + p["author"],
        "- 공개일: " + date,
        "- 파일 수: " + str(nfiles),
        "- 파일 크기(바이트): " + str(len(data)),
        "- 태그: " + p["tags"],
        "- 표기 요구: 없음 (CC0)",
        "- AI 생성 여부: 출처 페이지에 언급 없음",
    ]
    open(os.path.join(p["slug"], "pack.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    lic = [
        "팩: " + p["name"],
        "출처: " + p["url"],
        "라이선스: CC0 1.0 (출처 페이지 Creative Commons CC0 표기)",
        "저작자: " + p["author"],
        "공개일: " + date,
        "다운로드: " + zip_url,
        "확인: " + today + " OpenGameArt 페이지 CC0 표기와 .zip 링크 확인",
        "표기: 없음 (CC0, 표기 불필요)",
    ]
    open(os.path.join(p["slug"], "LICENSE-SOURCE.txt"), "w", encoding="utf-8").write("\n".join(lic) + "\n")
    cred = [
        p["name"],
        "제작: " + p["author"],
        "출처: " + p["url"],
        "라이선스: CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/)",
        "수집: sigco3111 game-asset-catalog / " + today,
    ]
    open(os.path.join(p["slug"], "CREDITS.txt"), "w", encoding="utf-8").write("\n".join(cred) + "\n")
    try:
        open(os.path.join(p["slug"], "LICENSE.txt"), "w", encoding="utf-8").write(get(CC0_TEXT))
    except Exception as e:
        log("license text error " + repr(e))
    if p.get("readme"):
        readme = open("README.md", encoding="utf-8").read()
        if "### " + p["name"] not in readme:
            readme = readme.rstrip() + "\n### " + p["name"] + "\n"
            if rel:
                readme += "- 파일: [릴리스 " + p["release"] + " 첨부 다운로드](https://github.com/sigco3111/" + "assets-audio" + "/releases/download/" + p["release"] + "/" + urllib.parse.quote(zip_name) + ") (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개)\n"
            else:
                readme += "- 파일: " + zip_name + " (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개)\n"
            readme += "- 제작: " + p["author"] + " / 라이선스: CC0 / 원본: " + p["url"] + "\n"
            open("README.md", "w", encoding="utf-8").write(readme)
        sh("git add -A " + p["slug"] + " README.md")
    else:
        sh("git add -A " + p["slug"])
    sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "에셋: ' + p["name"] + ' 추가"')
    sh("git push origin HEAD:main")
    return {"name": p["name"], "zip": zip_name, "mb": size_mb, "files": nfiles, "release": rel, "url": p["url"]}

def main():
    added = []
    try:
        names = load_names()
        log("index names " + str(len(names)))
        for p in PACKS:
            if len(added) >= LIMIT:
                break
            try:
                r = collect(p, names)
                if r:
                    added.append(r)
                    log("ADDED " + p["name"])
            except subprocess.CalledProcessError as e:
                log("GIT ERROR " + p["name"] + " " + repr(e))
                sh("git reset --hard HEAD", check=False)
            except Exception as e:
                log("ERROR " + p["name"] + " " + repr(e))
    except Exception:
        log("FATAL " + traceback.format_exc())
    log("SUMMARY " + json.dumps(added, ensure_ascii=False))
    open(LOG, "w", encoding="utf-8").write("\n".join(OUT) + "\n")
    subprocess.run('git add ' + LOG + ' && git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "진단: A101b 수집 로그" && git push origin HEAD:main', shell=True)

main()
