import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
    try:
        p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=10)
        return p.returncode==0,("ok" if p.returncode==0 else "failed")
    except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import mask_fields;assert mask_fields({\"user\":{\"password\":\"x\"}} ,{\"password\"})=={\"user\":{\"password\":\"***\"}}")
r2=run("from solution import mask_fields\nx={\"Rows\":[{\"TOKEN\":\"a\"},({\"token\":\"b\"},)]};assert mask_fields(x,{\"token\"})=={\"Rows\":[{\"TOKEN\":\"***\"},({\"token\":\"***\"},)]}")
r3=run("from solution import mask_fields\nx={\"keep\":[{\"secret\":\"x\"}]};y=mask_fields(x,{\"secret\"});y[\"keep\"].append(2);assert x=={\"keep\":[{\"secret\":\"x\"}]} and isinstance(y[\"keep\"],list)")
g=run("from solution import mask_fields\nx={\"count\":2,\"items\":[1,None]};assert mask_fields(x,{\"secret\"})==x")
env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]}
integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"}
requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}}
regressions={"G1":{"passed":g[0],"detail":g[1]}}
resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"feature-04","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
