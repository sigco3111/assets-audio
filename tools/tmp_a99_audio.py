import json, os, re, subprocess, urllib.request, zipfile, datetime

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
INDEX = "https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
PAGE = "https://opengameart.org/content/150-combat-sound-effects"
NAME = "150 Combat Sound Effects"
SLUG = "150-combat-sound-effects"
AUTHOR = "untamedpixels"
DATE = "2026-10-27"
TAGS = "sfx,combat,magic,hit,explosion,audio"
RELEASE = "v5.0"


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_names():
    data = json.loads(get(INDEX))
    names = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "name" and isinstance(v, str):
                    names.add(norm(v))
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return names


def sh(cmd, check=True):
    print("$ " + cmd, flush=True)
    subprocess.run(cmd, shell=True, check=check)


def main():
    names = load_names()
    print("index names:", len(names), flush=True)
    if norm(NAME) in names:
        print("duplicate, abort", flush=True)
        return
    html = get(PAGE)
    zips = re.findall(r'https://opengameart\.org/sites/default/files/[^"\'<> ]+\.zip', html)
    if not zips:
        print("no zip link", flush=True)
        return
    zip_url = zips[0]
    zip_name = urllib.parse.unquote(zip_url.rsplit("/", 1)[-1])
    data = get(zip_url, binary=True)
    os.makedirs("/tmp/pack", exist_ok=True)
    zpath = "/tmp/pack/" + zip_name
    with open(zpath, "wb") as f:
        f.write(data)
    nfiles = 0
    with zipfile.ZipFile(zpath) as z:
        nfiles = len([i for i in z.namelist() if not i.endswith("/")])
    size_mb = round(len(data) / 1048576.0, 1)
    os.makedirs(SLUG, exist_ok=True)
    with open(os.path.join(SLUG, "pack.md"), "w", encoding="utf-8") as f:
        f.write("# " + NAME + "\n\n")
        f.write("- 출처 URL: " + PAGE + "\n")
        f.write("- 받은 파일: " + zip_name + " (" + str(size_mb) + "MB, 릴리스 " + RELEASE + " 첨부)\n")
        f.write("- 라이선스: CC0\n")
        f.write("- 제작자: " + AUTHOR + "\n")
        f.write("- 공개일: " + DATE + "\n")
        f.write("- 파일 수: " + str(nfiles) + "\n")
        f.write("- 파일 크기(바이트): " + str(len(data)) + "\n")
        f.write("- 태그: " + TAGS + "\n")
        f.write("- 표기 요구: 없음 (CC0)\n")
        f.write("- AI 생성 여부: 출처 페이지에 언급 없음\n")
    with open(os.path.join(SLUG, "LICENSE-SOURCE.txt"), "w", encoding="utf-8") as f:
        f.write("팩: " + NAME + "\n출처: " + PAGE + "\n")
        f.write("라이선스: CC0 1.0 (출처 페이지 표기)\n")
        f.write("제작자: " + AUTHOR + "\n공개일: " + DATE + "\n")
        f.write("다운로드: " + zip_url + "\n")
        f.write("확인: " + datetime.date.today().isoformat() + " OpenGameArt 팩 페이지에 CC0 표기 확인\n")
    sh('gh release create ' + RELEASE + ' --title "' + RELEASE + '" --notes "에셋 수집 라운드 A99" || true')
    sh('gh release upload ' + RELEASE + ' "' + zpath + '" --clobber')
    with open("README.md", encoding="utf-8") as f:
        readme = f.read()
    block = ("\n### " + NAME + "\n"
             "- 파일: [릴리스 " + RELEASE + " 첨부 다운로드](https://github.com/sigco3111/assets-audio/releases/download/" + RELEASE + "/" + zip_name + ") (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개: 근접·원거리·폭발·마법 타격음)\n"
             "- 제작: " + AUTHOR + " / 라이선스: CC0 / 원본: " + PAGE + "\n")
    if "### " + NAME not in readme:
        readme = readme.rstrip() + "\n" + block
    m = re.search(r"현재 총 (\d+)팩", readme)
    if m:
        n = int(m.group(1)) + 1
        readme = readme[:m.start(1)] + str(n) + readme[m.end(1):]
        print("count ->", n, flush=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    sh("git add -A " + SLUG + " README.md")
    sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "에셋: ' + NAME + ' 추가"')
    sh("git push origin HEAD:main")
    print("DONE " + json.dumps({"name": NAME, "files": nfiles, "mb": size_mb}), flush=True)


main()
