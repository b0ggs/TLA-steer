import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=10);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("import os,subprocess,sys\ne=os.environ.copy();e[\"USER_NAME\"]=\"Ada\";p=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\"],input=\"Hi ${USER_NAME}!\",text=True,capture_output=True,env=e);assert p.stdout==\"Hi Ada!\"")
r2=run("import subprocess,sys\np=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\"],input=\"$$5 ${M2_DEFINITELY_MISSING}\",text=True,capture_output=True);assert p.stdout==\"$5 ${M2_DEFINITELY_MISSING}\"")
r3=run("import subprocess,sys\np=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\",\"--strict\"],input=\"${M2_Z} ${M2_A}\",text=True,capture_output=True);assert p.returncode==2 and p.stdout==\"\" and \"M2_A\" in p.stderr and \"M2_Z\" in p.stderr")
g=run("import subprocess,sys\np=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\"],input=\"plain\\ntext\",text=True,capture_output=True);assert p.stdout==\"plain\\ntext\"");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"integration-03","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
