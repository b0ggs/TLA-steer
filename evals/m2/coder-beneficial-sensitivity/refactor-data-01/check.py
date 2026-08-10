import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=4);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import dedupe_records\nassert dedupe_records([{\"id\":2,\"v\":\"a\"},{\"id\":1},{\"id\":2,\"v\":\"b\"}])==[{\"id\":2,\"v\":\"b\"},{\"id\":1}]")
r2=run("from solution import dedupe_records\nassert dedupe_records([{\"id\":1,\"a\":1},{\"id\":1,\"b\":2}])==[{\"id\":1,\"b\":2}]")
r3=run("from solution import dedupe_records\ntry:dedupe_records([{\"id\":1},{\"x\":2}]);raise AssertionError()\nexcept ValueError as e:assert \"1\" in str(e)")
g=run("from solution import dedupe_records\nx=[{\"id\":1,\"nested\":[]}];y=dedupe_records(x);y[0][\"nested\"].append(2);assert x==[{\"id\":1,\"nested\":[]}]");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"refactor-data-01","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
