import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=10);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import overlay_config\nassert overlay_config({\"db\":{\"host\":\"h\",\"port\":1},\"x\":2},{\"db\":{\"port\":3}})=={\"db\":{\"host\":\"h\",\"port\":3},\"x\":2}")
r2=run("from solution import overlay_config\nassert overlay_config({\"a\":1,\"nested\":{\"x\":1,\"y\":2}},{\"a\":None,\"nested\":{\"x\":None}})=={\"nested\":{\"y\":2}}")
r3=run("from solution import overlay_config\nd={\"x\":[1],\"n\":{\"a\":[]}};o={\"x\":[2]};r=overlay_config(d,o);r[\"x\"].append(3);r[\"n\"][\"a\"].append(1);assert d=={\"x\":[1],\"n\":{\"a\":[]}} and o=={\"x\":[2]}")
g=run("from solution import overlay_config\nd={\"a\":1,\"b\":{\"c\":2}};assert overlay_config(d,{})==d and d=={\"a\":1,\"b\":{\"c\":2}}");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"refactor-data-04","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
