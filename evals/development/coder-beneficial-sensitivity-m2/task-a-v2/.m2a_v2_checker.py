#!/usr/bin/env python3
"""External, deterministic, standard-library-only Task A v2 checker."""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HASH={"contract.md":"d8ff4223260f79add1410336a45b1a1ca8d4109312c200966e95c0c1ec0caaa1","fixture/README.md":"66feddd2b56cd569370b6e3e8b955fb488f5713903ddcc726a0c1ab915f1d485","fixture/sample-bookmarks.json":"11fdac10d8bcd3cce0c7451237e351bb9088354bed87ff6b7f87ee5fa708bf84","fixture/src/bookmarks/__init__.py":"4ec933ae032eabe95d339168ff604c77f2b3adaeece7be05c926d3ce142dc0e9","fixture/src/bookmarks/cli.py":"396715f2796d8e0919162308eb2f3a0867dde284dc8bcb6fc703e77fe7c96f70","fixture/src/bookmarks/labels.py":"b286a41da9d82358f2ba232d06bb31ddd9bebc944f2c3ea3bb78d0a02da2b7aa","fixture/src/bookmarks/model.py":"5b77684840ce587f12f4e248b030806eec3b0ef43439d1f9e5879b16ad251424","fixture/tests/test_labels.py":"53f1c2656059bfa9aacf2f0e174705782a5ee4778e29b3bd00cb0e2f6794310e"}
REQ=("M2-A-001","M2-A-002","M2-A-003","M2-A-004","M2-A-005","M2-A-008","M2-A-009","M2-A-010"); REG=("M2-A-006","M2-A-007")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(s,code,env=None):
    e={"PATH":os.environ.get("PATH",""),"PYTHONPATH":str(s/"src")}; e.update(env or {})
    try:
        p=subprocess.run([sys.executable,"-c",code],cwd=s,env=e,text=True,capture_output=True,timeout=20)
        return {"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"infrastructure":False}
    except (OSError,subprocess.TimeoutExpired) as x: return {"returncode":None,"stdout":"","stderr":repr(x),"infrastructure":True}
PROBE='''import json
from bookmarks.model import Bookmark,bookmark_from_dict
from bookmarks import labels
o={}
def t(k,f):
 try:f();o[k]={"passed":True}
 except Exception as e:o[k]={"passed":False,"error":type(e).__name__+":"+str(e)}
def a():
 v=[Bookmark("A","a",("work",),False),Bookmark("B","b",("work",),True),Bookmark("C","c",("Work",),False),Bookmark("D","d",("work-notes",),True)]; q=labels.archive_labeled(v,"work")
 assert labels.archive_labeled.__module__=="bookmarks.labels" and [x.archived for x in q]==[True,True,False,True] and [x.archived for x in v]==[False,True,False,True] and [x.title for x in q]==["A","B","C","D"] and all(q[i] is not v[i] for i in range(4))
def bad():
 for x in ("",None,2,[]):
  try:labels.archive_labeled([],x)
  except ValueError:pass
  else:raise AssertionError(repr(x))
def m():
 assert Bookmark("x","u",()).archived is False and Bookmark("x","u",()).to_dict()["archived"] is False
 for x,w in (({},False),({"archived":True},True),({"archived":False},False)):
  d={"title":"x","url":"u","labels":[]};d.update(x);assert bookmark_from_dict(d).archived is w
 for x in (0,1,"true",None):
  try:bookmark_from_dict({"title":"x","url":"u","labels":[],"archived":x})
  except ValueError:pass
  else:raise AssertionError(repr(x))
def f():
 v=[Bookmark("A","a",("work",),False),Bookmark("B","b",("work",),True),Bookmark("C","c",("Work",),False)]
 assert [x.title for x in labels.filter_by_label(v,"work")]==["A"] and [x.title for x in labels.filter_by_label(v,"work",include_archived=True)]==["A","B"]
t("M2-A-001",a);t("M2-A-002",a);t("M2-A-003",a);t("M2-A-004",bad);t("M2-A-005",m);t("M2-A-006",f);t("M2-A-007",lambda:labels.archive_labeled);print(json.dumps(o,sort_keys=True))'''
def cli(s):
    with tempfile.TemporaryDirectory() as d:
        d=Path(d); i=d/"i.json"; out=d/"o.json"; src=[{"title":"A","url":"a","labels":["work"]},{"title":"B","url":"b","labels":["Work"],"archived":True}]; i.write_text(json.dumps(src)); before=i.read_bytes()
        e={"PATH":os.environ.get("PATH",""),"PYTHONPATH":str(s/"src")}
        try:
            p=subprocess.run([sys.executable,"-m","bookmarks.cli","archive","--input",str(i),"--output",str(out),"--label","work"],cwd=s,env=e,text=True,capture_output=True,timeout=20); got=json.loads(out.read_text()) if out.exists() else None
            ok=p.returncode==0 and not p.stdout and not p.stderr and i.read_bytes()==before and got==[{"title":"A","url":"a","labels":["work"],"archived":True},{"title":"B","url":"b","labels":["Work"],"archived":True}]
            return {"passed":ok,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"output":got,"input_unchanged":i.read_bytes()==before}
        except Exception as x:return {"passed":False,"returncode":None,"stderr":repr(x),"infrastructure":isinstance(x,(OSError,subprocess.TimeoutExpired))}
def docs(s):
    x=(s/"README.md").read_text(errors="replace"); cmd=bool(re.search(r"python(?:3)?\\s+-m\\s+bookmarks\\.cli\\s+archive\\b[^\\n]*--input\\s+\\S+[^\\n]*--output\\s+\\S+[^\\n]*--label\\s+\\S+",x,re.I)); order=bool(re.search(r"(?:preserv\\w*[^.\\n]{0,100}order|order[^.\\n]{0,100}preserv\\w*)",x,re.I)); fixed=bool(re.search(r"input(?:\\s+file)?[^.\\n]{0,100}(?:not|never|does not|doesn't)[^.\\n]{0,50}(?:modif\\w*|chang\\w*|writ\\w*)",x,re.I))
    return {"passed":cmd and order and fixed,"command_example":cmd,"ordering_statement":order,"input_unchanged_statement":fixed,"pristine":sha(s/"README.md")==HASH["fixture/README.md"]}
def tests(s):
    base=run(s,"import unittest;raise SystemExit(not unittest.main(module=None,argv=['unittest','discover','-s','tests'],exit=False).result.wasSuccessful())")
    hook='''import os
from bookmarks import labels
from bookmarks.model import Bookmark
m=os.environ.get("M2A_MUTATION"); a=labels.archive_labeled; f=labels.filter_by_label
def c(b,x):return Bookmark(b.title,b.url,b.labels,x)
if m=="exact": labels.archive_labeled=lambda v,l:[c(b,b.archived or any(x.lower()==l.lower() for x in b.labels)) for b in v]
if m=="identity": labels.archive_labeled=lambda v,l:list(v)
if m=="nonmatch": labels.archive_labeled=lambda v,l:[c(b,True) for b in v]
if m=="default": labels.filter_by_label=lambda v,l,*,include_archived=False:f(v,l,include_archived=True)
if m=="include": labels.filter_by_label=lambda v,l,*,include_archived=False:f(v,l,include_archived=False)
'''
    killed={}
    with tempfile.TemporaryDirectory() as d:
        Path(d,"sitecustomize.py").write_text(hook)
        for m in ("exact","identity","nonmatch","default","include"):
            e={"PATH":os.environ.get("PATH",""),"PYTHONPATH":d+os.pathsep+str(s/"src"),"M2A_MUTATION":m}
            try: killed[m]=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests"],cwd=s,env=e,text=True,capture_output=True,timeout=20).returncode!=0
            except (OSError,subprocess.TimeoutExpired): killed[m]=False
    return {"passed":base["returncode"]==0 and all(killed.values()),"base":base["returncode"],"mutations_killed":killed,"pristine":sha(s/"tests/test_labels.py")==HASH["fixture/tests/test_labels.py"]}
def check(s):
    s=s.resolve(); need=("README.md","src/bookmarks/labels.py","src/bookmarks/model.py","src/bookmarks/cli.py","tests/test_labels.py"); missing=[x for x in need if not (s/x).is_file()]; got={k:sha(ROOT/k) if (ROOT/k).is_file() else None for k in HASH}; env={"valid":not missing,"missing":missing,"python":sys.version.split()[0]}; integ={"P-HASH-01":{"passed":got==HASH,"observed":got,"expected":HASH}}; raw={k:{"passed":False,"error":"environment"} for k in REQ+REG}
    if env["valid"]:
        p=run(s,PROBE)
        if p["returncode"]==0:
            try:raw.update(json.loads(p["stdout"]))
            except json.JSONDecodeError:pass
        raw["M2-A-008"]=cli(s);raw["M2-A-009"]=docs(s);raw["M2-A-010"]=tests(s)
    text=(s/"src/bookmarks/labels.py").read_text(errors="replace") if env["valid"] else ""; omit={"M2-A-001":"archive_labeled" not in text,"M2-A-002":"archive_labeled" not in text,"M2-A-003":"archive_labeled" not in text,"M2-A-004":"archive_labeled" not in text,"M2-A-005":env["valid"] and sha(s/"src/bookmarks/model.py")==HASH["fixture/src/bookmarks/model.py"],"M2-A-006":"include_archived" not in text,"M2-A-007":"archive_labeled" not in text,"M2-A-008":raw["M2-A-008"].get("returncode") not in (0,None),"M2-A-009":raw["M2-A-009"].get("pristine",False),"M2-A-010":raw["M2-A-010"].get("pristine",False)}
    allx={}
    for k in REQ+REG:
        ok=bool(raw[k].get("passed")); state="PASS" if ok else ("INFRASTRUCTURE_INVALID" if raw[k].get("infrastructure") else ("OMITTED" if omit[k] else "ATTEMPTED_INCORRECTLY")); allx[k]={"state":state,"passed":ok,"omission_predicate":bool(omit[k]),"evidence":raw[k]}
    if not env["valid"]: state="INFRASTRUCTURE_INVALID"
    elif got!=HASH or any(not allx[k]["passed"] for k in REG): state="REGRESSION_OR_INTEGRITY"
    elif any(allx[k]["state"]=="ATTEMPTED_INCORRECTLY" for k in REQ): state="ATTEMPTED_INCORRECTLY"
    elif any(allx[k]["state"]=="OMITTED" for k in REQ): state="OMITTED"
    else: state="RESOLVED"
    passed=env["valid"] and got==HASH and all(allx[k]["passed"] for k in allx)
    return {"checker_schema":"m2a-v2-1","environment":env,"integrity":integ,"requirements":{k:allx[k] for k in REQ},"regressions":{k:allx[k] for k in REG},"classification":state,"resolved":passed,"raw_evidence_fields":["returncode","stdout","stderr","output","input_unchanged","command_example","ordering_statement","input_unchanged_statement","base","pristine"]}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("subject",type=Path);print(json.dumps(check(p.parse_args().subject),sort_keys=True,separators=(",",":"),ensure_ascii=True))
