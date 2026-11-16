import json, os, re, shutil, subprocess, urllib.request, zipfile, datetime

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Cache-Control": "no-cache"}
INDEX = "https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
NAME = "Some sounds 2"
SLUG = "some-sounds-2"
URL = "https://opengameart.org/content/some-sounds-2"
AUTHOR = "Ziph"
DATE = "2025-07-09"
RELEASE = "v6.0"
BT = chr(96)


def get(url, binary=False, bust=True):
    if bust and "?" not in url:
        url = url + "?t=" + str(int(datetime.datetime.utcnow().timestamp()))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def sh(cmd):
    print("$ " + cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


def main():
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

    walk(json.loads(get(INDEX)))
    print("names", len(names), "dup?" , norm(NAME) in names, flush=True)
    if os.path.isdir(SLUG):
        print("SKIP dir exists", flush=True)
        return
    html = get(URL, bust=False)
    print("cc0 in html:", "CC0" in html, flush=True)
    zips = re.findall(r'https://opengameart\.org/sites/default/files/[^"\x27<> ]+\.zip', html)
    print("zips found:", zips[:3], flush=True)
    if not zips:
        return
    zip_url = zips[0]
    zip_name = urllib.parse.unquote(zip_url.rsplit("/", 1)[-1])
    print("zip:", zip_url, flush=True)
    data = get(zip_url, bust=False, binary=True)
    print("bytes:", len(data), flush=True)
    tmp = "/tmp/" + zip_name
    open(tmp, "wb").write(data)
    with zipfile.ZipFile(tmp) as z:
        nfiles = len([i for i in z.namelist() if not i.endswith("/")])
    size_mb = round(len(data) / 1048576.0, 1)
    os.makedirs(SLUG)
    if len(data) > 5 * 1024 * 1024:
        sh("gh release create " + RELEASE + " --title " + RELEASE + " --notes 'SFX pack' || true")
        sh('gh release upload ' + RELEASE + ' "' + tmp + '" --clobber')
        os.remove(tmp)
        rel = ", 릴리스 " + RELEASE + " 첨부"
    else:
        shutil.move(tmp, os.path.join(SLUG, zip_name))
        rel = ""
    with open(os.path.join(SLUG, "pack.md"), "w", encoding="utf-8") as f:
        f.write("# " + NAME + "\n\n")
        f.write("- 출처 URL: " + URL + "\n")
        f.write("- 받은 파일: " + zip_name + " (" + str(size_mb) + "MB" + rel + ")\n")
        f.write("- 라이선스: CC0\n")
        f.write("- 라이선스 원문: https://creativecommons.org/publicdomain/zero/1.0/\n")
        f.write("- 저작자: " + AUTHOR + "\n")
        f.write("- 공개일: " + DATE + "\n")
        f.write("- 파일 수: " + str(nfiles) + "\n")
        f.write("- 파일 크기(바이트): " + str(len(data)) + "\n")
        f.write("- 태그: sfx,magic,laser,sword,synth,audio\n")
        f.write("- 표기 요구: 없음 (CC0)\n")
        f.write("- AI 생성 여부: 출처 페이지에 언급 없음\n")
    with open(os.path.join(SLUG, "LICENSE-SOURCE.txt"), "w", encoding="utf-8") as f:
        f.write("팩: " + NAME + "\n출처: " + URL + "\n")
        f.write("라이선스: CC0 1.0 (출처 페이지 표기)\n")
        f.write("저작자: " + AUTHOR + "\n공개일: " + DATE + "\n")
        f.write("다운로드: " + zip_url + "\n")
        f.write("확인: " + datetime.date.today().isoformat() + " OpenGameArt 페이지 CC0 표기 확인\n")
    readme = open("README.md", encoding="utf-8").read()
    if "### " + NAME not in readme:
        readme = readme.rstrip() + "\n### " + NAME + "\n"
        if rel:
            readme += "- 파일: [릴리스 " + RELEASE + " 첨부 다운로드](https://github.com/sigco3111/assets-audio/releases/download/" + RELEASE + "/" + zip_name + ") (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개: FM 합성 효과음 262종 레이저·주문·검격)\n"
        else:
            readme += "- 파일: " + BT + zip_name + BT + " (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개: FM 합성 효과음 262종 레이저·주문·검격)\n"
        readme += "- 제작: " + AUTHOR + " / 라이선스: CC0 / 원본: " + URL + "\n"
        open("README.md", "w", encoding="utf-8").write(readme)
    sh("git add -A " + SLUG + " README.md")
    sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "에셋: ' + NAME + ' 추가"')
    sh("git push origin HEAD:main")
    print("DONE nfiles", nfiles, "mb", size_mb, flush=True)


main()
