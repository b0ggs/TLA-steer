import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
    try:
        p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=4)
        return p.returncode==0,("ok" if p.returncode==0 else "failed")
    except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import apply_operations;assert apply_operations({\"a\":3},[(\"add\",\"a\",2),(\"remove\",\"a\",4),(\"add\",\"b\",1)])=={\"a\":1,\"b\":1}")
r2=run("from solution import apply_operations\nx={\"a\":2}\ntry: apply_operations(x,[(\"remove\",\"a\",1),(\"remove\",\"a\",2)]);raise AssertionError()\nexcept ValueError: pass\nassert x=={\"a\":2}")
r3=run("from solution import apply_operations\nfor ops in ([(\"drop\",\"a\",1)],[(\"add\",\"a\",-1)]):\n try: apply_operations({},ops);raise AssertionError()\n except ValueError: pass")
g=run("from solution import apply_operations\nx={\"a\":1};assert apply_operations(x,[(\"add\",\"a\",1)])=={\"a\":2} and x=={\"a\":1}")
env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]}
integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"}
requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}}
regressions={"G1":{"passed":g[0],"detail":g[1]}}
resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"bug-04","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
