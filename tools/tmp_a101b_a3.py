import json,os,re,shutil,subprocess as S,urllib.request as U,urllib.parse as P,zipfile as Z,datetime as D
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Chrome/124"}
IX="https://raw.githubusercontent.com/sigco3111/game-asset-catalog/main/assets-index.min.json"
CC="https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt"
LOG="tools/a101b_log.txt"
O=[]
PACKS=[
 {"slug":"8-bit-sound-effect-pack-vol-001","name":"8-Bit Sound Effect Pack (Vol. 001)","url":"https://opengameart.org/content/8-bit-sound-effect-pack-vol-001","author":"Deva","tags":"sfx,8bit,retro,audio","rel":"v7.0"},
 {"slug":"100-cc0-sfx","name":"100 CC0 SFX","url":"https://opengameart.org/content/100-cc0-sfx","author":"rubberduck","tags":"sfx,audio","rel":"v7.1"},
 {"slug":"8-bit-sound-effect-pack","name":"8-Bit Sound Effect Pack","url":"https://opengameart.org/content/8-bit-sound-effect-pack","author":"OwlishMedia","tags":"sfx,8bit,retro,audio","rel":"v7.2"},
]
def lg(s):
 print(s,flush=True);O.append(str(s))
def g(u,b=0):
 r=U.urlopen(U.Request(u,headers=UA),timeout=600).read()
 return r if b else r.decode("utf-8","replace")
def n(s):
 return re.sub(r"[^a-z0-9]","",s.lower())
def nm():
 o=set()
 def w(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k=="name" and isinstance(v,str):
     o.add(n(v));o.add(re.sub(r"[0-9]+$","",n(v)))
    else:
     w(v)
  elif isinstance(x,list):
   for v in x:
    w(v)
 w(json.loads(g(IX)))
 return o
def sh(c,ck=1):
 lg("$ "+c);S.run(c,shell=True,check=ck)
def go(p,s):
 if n(p["name"]) in s:
  lg("DUP "+p["name"]);return
 if os.path.isdir(p["slug"]):
  lg("DIR "+p["slug"]);return
 h=g(p["url"])
 lg("page %d cc0 %s"%(len(h),"CC0" in h))
 if "CC0" not in h:
  return
 zs=re.findall(r'https://opengameart\.org/sites/default/files/[^"\'<> ]+\.zip',h)
 lg("zips "+json.dumps(zs[:4]))
 zs=[z for z in zs if "preview" not in z.lower() and "demo" not in z.lower()]
 if not zs:
  return
 zu=zs[0];zn=P.unquote(zu.rsplit("/",1)[-1]);dt=g(zu,1)
 t="/tmp/x.zip";open(t,"wb").write(dt)
 zf=Z.ZipFile(t);nf=len([i for i in zf.namelist() if not i.endswith("/")])
 mb=round(len(dt)/1048576.0,1)
 m=re.search(r'article:published_time" content="(\d{4}-\d{2}-\d{2})',h)
 dd=m.group(1) if m else "출처 페이지 표기 미확인"
 os.makedirs(p["slug"]);rel=""
 if len(dt)>5*1024*1024:
  sh("gh release create "+p["rel"]+" --title '"+p["name"]+"' --notes zip || true",0)
  sh("gh release upload "+p["rel"]+' "'+t+'" --clobber')
  os.remove(t);rel=", 릴리스 "+p["rel"]+" 첨부"
 else:
  shutil.move(t,os.path.join(p["slug"],zn))
 L=["# "+p["name"],"","- 출처 URL: "+p["url"],
  "- 받은 파일: "+zn+" ("+str(mb)+"MB"+rel+")","- 라이선스: CC0",
  "- 라이선스 원문: https://creativecommons.org/publicdomain/zero/1.0/",
  "- 저작자: "+p["author"],"- 공개일: "+dd,"- 파일 수: "+str(nf),
  "- 파일 크기(바이트): "+str(len(dt)),"- 태그: "+p["tags"],
  "- 표기 요구: 없음 (CC0)","- AI 생성 여부: 출처 페이지에 언급 없음"]
 open(p["slug"]+"/pack.md","w",encoding="utf-8").write("\n".join(L)+"\n")
 C=["팩: "+p["name"],"출처: "+p["url"],"라이선스: CC0 1.0 (출처 페이지 표기)",
  "저작자: "+p["author"],"공개일: "+dd,"다운로드: "+zu,
  "확인: "+D.date.today().isoformat()+" OpenGameArt 페이지 CC0 표기와 .zip 링크 확인","표기: 없음"]
 open(p["slug"]+"/LICENSE-SOURCE.txt","w",encoding="utf-8").write("\n".join(C)+"\n")
 open(p["slug"]+"/CREDITS.txt","w",encoding="utf-8").write("\n".join([p["name"],"제작: "+p["author"],"출처: "+p["url"],"라이선스: CC0 1.0","수집: sigco3111 game-asset-catalog"])+"\n")
 try:
  open(p["slug"]+"/LICENSE.txt","w",encoding="utf-8").write(g(CC))
 except Exception as e:
  lg("lic "+repr(e))
 R=open("README.md",encoding="utf-8").read()
 if "### "+p["name"] not in R:
  R=R.rstrip()+"\n### "+p["name"]+"\n- 파일: "+zn+" ("+str(mb)+"MB"+(rel or ", 저장소 포함")+", 파일 "+str(nf)+"개)\n- 제작: "+p["author"]+" / 라이선스: CC0 / 원본: "+p["url"]+"\n"
  open("README.md","w",encoding="utf-8").write(R)
 sh("git add -A "+p["slug"]+" README.md")
 sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "에셋: '+p["name"]+' 추가"')
 sh("git push origin HEAD:main")
 lg("ADDED "+p["name"]+" "+zn+" "+str(mb)+"MB "+str(nf))
def main():
 try:
  s=nm();lg("names %d"%len(s))
  c=0
  for p in PACKS:
   if c>=2:break
   try:
    if os.path.isdir(p["slug"]):lg("DIR "+p["slug"]);continue
    if n(p["name"]) in s:lg("DUP "+p["name"]);continue
    go(p,s);c+=1
   except Exception as e:
    lg("ERR "+p["name"]+" "+repr(e));sh("git reset --hard HEAD",0)
 except Exception as e:
  lg("FATAL "+repr(e))
 open(LOG,"w",encoding="utf-8").write("\n".join(O)+"\n")
 S.run('git add '+LOG+' && git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "진단: A101b 로그" && git push origin HEAD:main',shell=True)
main()
