import json,subprocess,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit(2)
root=Path(sys.argv[1]);target=root/"solution.py"
def run(code):
 try:
  p=subprocess.run([sys.executable,"-I","-c","import sys;sys.path.insert(0,sys.argv[1]);"+code,str(root)],text=True,capture_output=True,timeout=4);return p.returncode==0,("ok" if p.returncode==0 else "failed")
 except subprocess.TimeoutExpired:return False,"timeout"
r1=run("from solution import coerce_rows\nout,e=coerce_rows([{\"age\":\"3\",\"extra\":1}],{\"age\":(int,0),\"name\":(str,\"\")});assert out==[{\"age\":3,\"name\":\"\"}] and e==[]")
r2=run("from solution import coerce_rows\ndefault=[];out,_=coerce_rows([{},{\"x\":None}],{\"x\":(str,default)});out[0][\"x\"].append(1);assert out[1][\"x\"]==[] and default==[]")
r3=run("from solution import coerce_rows\ns={\"a\":(int,0),\"b\":(int,9)};out,e=coerce_rows([{\"a\":\"x\",\"b\":\"y\"},{\"a\":\"z\",\"b\":\"2\"}],s);assert out==[{\"a\":0,\"b\":9},{\"a\":0,\"b\":2}] and e==[(0,\"a\",\"x\"),(0,\"b\",\"y\"),(1,\"a\",\"z\")]")
g=run("from solution import coerce_rows\nrows=[{\"x\":\"1\"}];s={\"x\":(int,0)};assert coerce_rows([],s)==([],[]) and coerce_rows(rows,{})==([{}],[]) and rows==[{\"x\":\"1\"}]");env={"passed":root.is_dir() and target.is_file(),"checks":["subject directory","solution.py present","isolated subprocess timeout"]};integrity={"passed":target.is_file(),"detail":"solution.py present" if target.is_file() else "solution.py missing"};requirements={"R1":{"passed":r1[0],"detail":r1[1]},"R2":{"passed":r2[0],"detail":r2[1]},"R3":{"passed":r3[0],"detail":r3[1]}};regressions={"G1":{"passed":g[0],"detail":g[1]}};resolved=env["passed"] and integrity["passed"] and all(x["passed"] for x in requirements.values()) and g[0]
print(json.dumps({"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"refactor-data-05","environment":env,"requirements":requirements,"regressions":regressions,"integrity":integrity,"resolved":resolved},sort_keys=True,separators=(",",":")))
