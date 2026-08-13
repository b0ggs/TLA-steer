import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=10);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("import subprocess,sys\np=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\"],input=\"b\\na\\nb\\n\",text=True,capture_output=True);assert p.stdout==\"b\\na\\n\"")
r2=run("import subprocess,sys\np=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\",\"-i\"],input=\"Alpha\\nALPHA\\nbeta\\n\",text=True,capture_output=True);assert p.stdout==\"Alpha\\nbeta\\n\"")
r3=run("import subprocess,sys,tempfile,pathlib\nwith tempfile.TemporaryDirectory() as d:\n f=pathlib.Path(d)/\"x\";f.write_text(\"a\\nb\\na\\n\");p=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\",\"--count\",str(f)],text=True,capture_output=True);assert p.stdout==\"2\\ta\\n1\\tb\\n\"")
g=run("import subprocess,sys\nfor data,want in ((\"\", \"\"),(\"x\",\"x\\n\")):\n p=subprocess.run([sys.executable,sys.argv[1]+\"/solution.py\"],input=data,text=True,capture_output=True);assert p.stdout==want");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"integration-02","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
