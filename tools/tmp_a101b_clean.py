import os,glob,subprocess as S
def sh(c,ck=1):
 print(c,flush=True);S.run(c,shell=True,check=ck)
t=glob.glob("tools/tmp_a101b*")+glob.glob("tools/a101b*")+glob.glob(".github/workflows/tmp-a101b*")
print("remove "+str(t),flush=True)
for x in t:
 sh("git rm -q -r "+x,0)
sh('git -c user.name="sigco3111" -c user.email="sigco3111k@gmail.com" commit -m "정리: A101b 임시 파일 삭제"',0)
sh("git push origin HEAD:main",0)
print("done",flush=True)
