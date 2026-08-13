import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=10);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import group_events\nx=[{\"timestamp\":\"2024-01-02T00:30:00+01:00\",\"v\":1},{\"timestamp\":\"2024-01-01T23:40:00Z\",\"v\":2}];assert list(group_events(x))==[\"2024-01-01\"]")
r2=run("from solution import group_events\nx=[{\"timestamp\":\"2024-02-01T00:00:00+00:00\"},{\"timestamp\":\"2024-01-01T00:00:00Z\"}];assert list(group_events(x))==[\"2024-01-01\",\"2024-02-01\"]")
r3=run("from solution import group_events\nx=[{\"timestamp\":\"2024-01-01T01:00:00Z\",\"v\":2},{\"timestamp\":\"2024-01-01T00:00:00Z\",\"v\":1},{\"timestamp\":\"2024-01-01T00:00:00+00:00\",\"v\":3}];assert [r[\"v\"] for r in group_events(x)[\"2024-01-01\"]]==[1,3,2]")
g=run("from solution import group_events\nx=[{\"timestamp\":\"2024-01-01T00:00:00Z\",\"nested\":[]}];y=group_events(x);y[\"2024-01-01\"][0][\"nested\"].append(1);assert x==[{\"timestamp\":\"2024-01-01T00:00:00Z\",\"nested\":[]}]");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"refactor-data-02","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
