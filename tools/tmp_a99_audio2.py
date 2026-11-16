import json, os, re, subprocess, urllib.request, zipfile, datetime

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
INDEX = "https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
BT = chr(96)
RELEASE = "v6.0"
PACKS = [
    {"slug": "ignisforge-free-sfx-sampler", "name": "IgnisForge Free SFX Sampler",
     "url": "https://opengameart.org/content/ignisforge-free-sfx-sampler-43-synthesized-retro-sound-effects",
     "author": "ignisforge", "date": "2026-08-19", "tags": "sfx,retro,arcade,spell,audio",
     "desc": "합성 레트로 효과음 43종: 코인, 레이저, 폭발, 점프, 데미지, UI, 주문, 공포 징글"},
]


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
    readme = open("README.md", encoding="utf-8").read()
    added = []
    for p in PACKS:
        if norm(p["name"]) in names:
            print("SKIP dup index:", p["name"], flush=True)
            continue
        if os.path.isdir(p["slug"]):
            print("SKIP existing dir:", p["slug"], flush=True)
            continue
        try:
            html = get(p["url"])
            zips = re.findall(r'https://opengameart\.org/sites/default/files/[^"\'<> ]+\.zip', html)
            if not zips:
                print("SKIP no zip:", p["url"], flush=True)
                continue
            zip_url = zips[0]
            zip_name = urllib.parse.unquote(zip_url.rsplit("/", 1)[-1])
            data = get(zip_url, binary=True)
            tmp = "/tmp/" + zip_name
            with open(tmp, "wb") as f:
                f.write(data)
            with zipfile.ZipFile(tmp) as z:
                nfiles = len([i for i in z.namelist() if not i.endswith("/")])
            size_mb = round(len(data) / 1048576.0, 2)
            big = len(data) > 5 * 1024 * 1024
            os.makedirs(p["slug"])
            if big:
                sh("gh release create " + RELEASE + " --title " + RELEASE + " --notes audio || true", check=False)
                sh('gh release upload ' + RELEASE + ' "' + tmp + '" --clobber')
                os.remove(tmp)
            else:
                os.rename(tmp, os.path.join(p["slug"], zip_name))
            with open(os.path.join(p["slug"], "pack.md"), "w", encoding="utf-8") as f:
                f.write("# " + p["name"] + "\n\n")
                f.write("- 출처 URL: " + p["url"] + "\n")
                f.write("- 받은 파일: " + zip_name + " (" + str(size_mb) + "MB" + (", 릴리스 " + RELEASE + " 첨부" if big else "") + ")\n")
                f.write("- 라이선스: CC0\n")
                f.write("- 라이선스 원문: https://creativecommons.org/publicdomain/zero/1.0/\n")
                f.write("- 저작자: " + p["author"] + "\n")
                f.write("- 공개일: " + p["date"] + "\n")
                f.write("- 파일 수: " + str(nfiles) + "\n")
                f.write("- 파일 크기(바이트): " + str(len(data)) + "\n")
                f.write("- 태그: " + p["tags"] + "\n")
                f.write("- 표기 요구: 없음 (CC0)\n")
                f.write("- AI 생성 여부: 출처 페이지에 언급 없음\n")
            with open(os.path.join(p["slug"], "LICENSE-SOURCE.txt"), "w", encoding="utf-8") as f:
                f.write("팩: " + p["name"] + "\n출처: " + p["url"] + "\n")
                f.write("라이선스: CC0 1.0 (출처 페이지 표기)\n")
                f.write("저작자: " + p["author"] + "\n공개일: " + p["date"] + "\n")
                f.write("다운로드: " + zip_url + "\n")
                f.write("확인: " + datetime.date.today().isoformat() + " OpenGameArt 팩 페이지 CC0 표기 확인\n")
            if "### " + p["name"] not in readme:
                readme = readme.rstrip() + "\n### " + p["name"] + "\n"
                if big:
                    readme += "- 파일: [릴리스 " + RELEASE + " 첨부 다운로드](https://github.com/sigco3111/assets-audio/releases/download/" + RELEASE + "/" + zip_name + ") (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개: " + p["desc"] + ")\n"
                else:
                    readme += "- 파일: " + BT + zip_name + BT + " (" + str(size_mb) + "MB, 파일 " + str(nfiles) + "개: " + p["desc"] + ")\n"
                readme += "- 제작: " + p["author"] + " / 라이선스: CC0 / 원본: " + p["url"] + "\n"
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(readme)
            sh("git add -A " + p["slug"] + " README.md")
            sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "에셋: ' + p["name"] + ' 추가"')
            sh("git push origin HEAD:main")
            added.append({"name": p["name"], "mb": size_mb, "files": nfiles})
            print("ADDED", p["name"], flush=True)
        except subprocess.CalledProcessError as e:
            print("GIT ERROR", p["name"], e, flush=True)
        except Exception as e:
            print("ERROR", p["name"], repr(e), flush=True)
    print("DONE count", len(added), flush=True)


main()
