import errno,hashlib,inspect,json,os,platform,pydoc,re,shutil,site,socket,stat,sys,tokenize
IDS={"real-boltons-indexed-slice","real-cpython-doctest-notes","real-cpython-enum-lookup","real-tomli-dotted-keys"}
LITERALS={"real-cpython-doctest-notes":"filesystem:doctest.py","real-cpython-enum-lookup":"enum.Enum.__new__","real-tomli-dotted-keys":"tomllib._parser"}
RUNTIME={"/":"overlay","/proc":"proc","/dev":"tmpfs","/dev/pts":"devpts","/sys":"sysfs","/sys/fs/cgroup":"cgroup2","/dev/mqueue":"mqueue","/dev/shm":"tmpfs","/etc/resolv.conf":"ext4","/etc/hostname":"ext4","/etc/hosts":"ext4","/proc/bus":"proc","/proc/fs":"proc","/proc/irq":"proc","/proc/sys":"proc","/proc/sysrq-trigger":"proc","/proc/acpi":"tmpfs","/proc/interrupts":"tmpfs","/proc/kcore":"tmpfs","/proc/keys":"tmpfs","/proc/latency_stats":"tmpfs","/proc/timer_list":"tmpfs","/proc/scsi":"tmpfs","/sys/firmware":"tmpfs"}
REQUIRED={"/","/proc","/dev","/dev/pts","/sys","/sys/fs/cgroup","/dev/mqueue","/dev/shm","/etc/resolv.conf","/etc/hostname","/etc/hosts"}; BINDS={"/workspace":"rw","/python":"ro","/agent-home":"rw"}; BAD=[]; CONTAM=[]
def emit(check,status,**fields): print(json.dumps({"check":check,"status":status,**fields},sort_keys=True,separators=(",",":")),flush=True)
def mark(check,good,**fields): BAD.append(check) if not good else None; emit(check,"PASS" if good else "FAIL",**fields)
def hit(check,**fields): CONTAM.append(check); emit(check,"CONTAMINATION_FOUND",**fields)
def sha(value): return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()
def norm(value): return "".join(c for c in value if not c.isspace())
def file_sha(path): return sha(open(path,"rb").read())
def py_source(path):
 fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
 with os.fdopen(fd,"rb") as stream: encoding,first=tokenize.detect_encoding(stream.readline); return (b"".join(first)+stream.read()).decode(encoding)
def argv_sha(argv): return sha(b"\0".join(os.fsencode(x) for x in argv)+b"\0")
def need(value,message): return value or (_ for _ in ()).throw(ValueError(message))
def identity(image=None): return {"canonical_executable":os.path.realpath(sys.executable),"version":sys.version,"executable_sha256":file_sha(os.path.realpath(sys.executable)),"image_digest":image,"path_resolution":shutil.which("python3")}
def policy_shape(argv):
 starts=[i for i,x in enumerate(argv) if x=="--sandbox-policy-cwd"]; ends=[i for i,x in enumerate(argv) if x=="--apply-seccomp-then-exec"]
 need(len(starts)==len(ends)==1 and starts[0]<ends[0],"non-unique policy bounds"); part=argv[starts[0]:ends[0]+1]
 need(sum(os.path.basename(x)=="bwrap" for x in argv)==sum("codex-linux-sandbox" in os.path.basename(x) for x in argv)==1,"non-unique bwrap/helper"); need("--use-legacy-landlock" not in argv,"legacy Landlock")
 for flag in ("--sandbox-policy-cwd","--command-cwd"): need(part.count(flag)==1 and part[part.index(flag)+1]=="/workspace",flag)
 need(part.count("--permission-profile")==1,"permission profile")
 profile=json.loads(part[part.index("--permission-profile")+1]); flat=norm(json.dumps(profile,sort_keys=True)).lower().replace("-","").replace("_","")
 need('"type":"managed"' in flat and '"path":"/workspace"' in flat and '"access":"write"' in flat and '"network":"restricted"' in flat,"profile is not network-free workspace-write")
 return part,profile
def policy_child():
 try:
  target=[sys.argv[2],int(sys.argv[3])]; status=open("/proc/self/status",encoding="utf-8").read(); ppid=int(re.search(r"^PPid:\s*(\d+)$",status,re.M).group(1)); raw=open(f"/proc/{ppid}/cmdline","rb").read(); parent=[os.fsdecode(x) for x in raw.rstrip(b"\0").split(b"\0")]; policy,profile=policy_shape(parent)
 except Exception as exc: emit("policy_child","FAIL",error=f"{type(exc).__name__}: {exc}"); return 2
 record={"identity":identity(sys.argv[4] if len(sys.argv)>4 else None),"parent_argv":parent,"permission_profile":profile,"policy_argv":policy,"policy_sha256":argv_sha(policy),"socket_target":target}
 try: connection=socket.create_connection((target[0],target[1]),timeout=5); connection.close(); emit("policy_child","FAIL",**record,denial=None,exit_status=0); return 2
 except PermissionError as exc: explicit=exc.errno==errno.EPERM; emit("policy_child","DENIED" if explicit else "FAIL",**record,denial=f"PermissionError: {exc}",exit_status=exc.errno); return 0 if explicit else 2
 except Exception as exc: emit("policy_child","FAIL",**record,denial=f"{type(exc).__name__}: {exc}",exit_status=getattr(exc,"errno",2)); return 2
def valid_item(item): return isinstance(item,dict) and set(item)=={"answer_bearing_modules","fix_signature_strings","interpreter_pin"} and isinstance(item["answer_bearing_modules"],list) and bool(item["answer_bearing_modules"]) and all(isinstance(x,str) and x and (x=="filesystem:doctest.py" or re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*",x)) for x in item["answer_bearing_modules"]) and isinstance(item["fix_signature_strings"],list) and bool(item["fix_signature_strings"]) and all(isinstance(x,str) and len(norm(x))>=20 for x in item["fix_signature_strings"]) and isinstance(item["interpreter_pin"],str) and re.fullmatch(r"\d+\.\d+\.\d+",item["interpreter_pin"])
def load_spec(path):
 try:
  need(not stat.S_ISLNK(os.lstat(path).st_mode),"spec is symlink"); raw=open(path,"rb").read(); data=json.loads(raw); problems=[]
  problems += ["task ids"] if not isinstance(data,dict) or set(data)!=IDS else []
  problems += [task+": entry" for task in IDS if not valid_item(data.get(task) if isinstance(data,dict) else None)]
  if isinstance(data,dict): problems += [task+": literal "+target for task,target in LITERALS.items() if target not in data.get(task,{}).get("answer_bearing_modules",[])]
  digest=sha(raw); emit("spec_validation","PASS" if not problems else "FAIL",problems=problems,spec_sha256=digest,task_ids=sorted(data) if isinstance(data,dict) else []); return (data,digest) if not problems else (None,digest)
 except Exception as exc: emit("spec_validation","FAIL",error=f"{type(exc).__name__}: {exc}",spec_sha256=None); return None,None
def resolve(target): return pydoc.locate(target) or need(False,target)
def inspect_targets(item):
 signatures=[(sha(x),norm(x)) for x in item["fix_signature_strings"]]
 for target in item["answer_bearing_modules"]:
  if target.startswith("filesystem:"): continue
  try: source=norm(inspect.getsource(resolve(target))); matches=[digest for digest,needle in signatures if needle in source]
  except Exception as exc: mark("literal_target",True,target=target,source_available=False,error=f"{type(exc).__name__}: {exc}"); continue
  hit("literal_target",target=target,source_available=True,signature_sha256=matches) if matches else mark("literal_target",True,target=target,source_available=True,signature_sha256=[])
def scan(item,workspace,mode):
 signatures=[(sha(x),norm(x)) for x in item["fix_signature_strings"]]; skip={"/proc","/sys","/dev",workspace}; errors=[]; matches=[]; doctests=[]; files=decoded=0
 if mode=="host" and CONTAM: emit("global_signature_scan","SKIPPED_AFTER_CONTAMINATION",decoded_file_count=0,file_count=0,matches=[],skipped_roots=sorted(skip)); return
 def walk_error(exc): errors.append(f"walk:{getattr(exc,'filename',None)}:{type(exc).__name__}:{exc}")
 for root,dirs,names in os.walk("/",topdown=True,onerror=walk_error,followlinks=False):
  kept=[]
  for name in dirs:
   if (path:=os.path.normpath(os.path.join(root,name))) in skip: continue
   try:
    if not stat.S_ISLNK(os.lstat(path).st_mode): kept.append(name)
   except Exception as exc: errors.append(f"stat:{path}:{type(exc).__name__}:{exc}")
  dirs[:]=kept
  for name in (x for x in names if x.endswith(".py")):
   path=os.path.join(root,name)
   try:
    if not stat.S_ISREG(os.lstat(path).st_mode): continue
    files+=1; text=norm(py_source(path)); decoded+=1; found=[digest for digest,needle in signatures if needle in text]
    doctests.append(path) if name=="doctest.py" else None; matches.append({"path":path,"signature_sha256":found}) if found else None
   except Exception as exc: errors.append(f"read:{path}:{type(exc).__name__}:{exc}")
 fields={"decoded_file_count":decoded,"file_count":files,"skipped_roots":sorted(skip)}; hit("global_signature_scan",matches=matches,**fields) if matches else mark("global_signature_scan",True,matches=[],**fields)
 mark("global_scan_errors",not errors,error_count=len(errors),error_sha256=sha("\n".join(errors)),error_sample=errors[:20])
 if "filesystem:doctest.py" in item["answer_bearing_modules"]: contaminated=[x for x in matches if os.path.basename(x["path"])=="doctest.py"]; hit("doctest_filesystem_search",candidates=doctests,matches=contaminated) if contaminated else mark("doctest_filesystem_search",True,candidates=doctests,matches=[])
def mount_check():
 try:
  rows=[]
  for line in open("/proc/self/mountinfo",encoding="utf-8"):
   left,right=line.rstrip("\n").split(" - ",1); a=left.split(); b=right.split(); unescape=lambda x:re.sub(r"\\([0-7]{3})",lambda m:chr(int(m.group(1),8)),x)
   need(len(a)>=6 and len(b)>=3,"short mountinfo row"); rows.append({"target":unescape(a[4]),"root":unescape(a[3]),"options":sorted(a[5].split(",")),"fstype":b[0],"source":unescape(b[1]),"super_options":sorted(b[2].split(","))})
  rows.sort(key=lambda x:(x["target"],x["root"],x["fstype"])); targets=[x["target"] for x in rows]
  wrong=[row for row in rows if not ((row["target"] in BINDS and BINDS[row["target"]] in row["options"]) or (row["target"] in RUNTIME and row["fstype"]==RUNTIME[row["target"]]))]
  mark("mount_table",not wrong and len(targets)==len(set(targets)) and (set(BINDS)|REQUIRED)<=set(targets),mounts=rows,unexpected=wrong)
 except Exception as exc: mark("mount_table",False,error=f"{type(exc).__name__}: {exc}",mounts=[])
def environment_check(item):
 secret=re.compile(r"TOKEN|SECRET|PASSWORD|PASSWD|COOKIE|CREDENTIAL|AUTH|(^|_)KEY($|_)",re.I); env={k:("<redacted:sha256:"+sha(v)+">" if secret.search(k) else v) for k,v in os.environ.items()}; markers=("/Users/","/Applications/","/Volumes/","/private/","/Library/Frameworks/","/Users/wade/Documents/MDs_EVAL")
 hits=[{"key":k,"marker":m} for k,v in os.environ.items() for m in markers if m in v]+[{"sys_path":p,"marker":m} for p in sys.path for m in markers if m in p]; packages={}
 try:
  for path in set(site.getsitepackages())|{p for p in sys.path if os.path.basename(p)=="site-packages"}: packages[path]=sorted(os.listdir(path)) if os.path.isdir(path) else []
  mark("environment",not hits and not any(packages.values()),environment=env,host_path_hits=hits,site_packages=packages,sys_path=sys.path)
 except Exception as exc: mark("environment",False,environment=env,error=f"{type(exc).__name__}: {exc}",host_path_hits=hits,sys_path=sys.path)
 home=os.environ.get("HOME"); code_home=os.environ.get("CODEX_HOME"); errors=[]; instructions=[]
 try:
  if home!="/agent-home" or code_home!=home or os.path.realpath(home)!=home or stat.S_ISLNK(os.lstat(home).st_mode): errors.append("HOME/CODEX_HOME")
  entries=set(os.listdir(home)); extra=entries-{"auth.json"}; session=next(iter(extra)) if len(extra)==1 else None; errors.append("topology") if entries!={"auth.json",session} or not session or not stat.S_ISREG(os.lstat(home+"/auth.json").st_mode) or stat.S_ISLNK(os.lstat(home+"/auth.json").st_mode) else None
  session_path=os.path.join(home,session) if session else home; errors.append("session") if not stat.S_ISDIR(os.lstat(session_path).st_mode) or stat.S_ISLNK(os.lstat(session_path).st_mode) or os.listdir(session_path) else None
  for root,dirs,names in os.walk(home,onerror=lambda exc:errors.append(f"walk:{type(exc).__name__}:{exc}"),followlinks=False):
   depth=os.path.relpath(root,home).count(os.sep)+(root!=home); dirs.__setitem__(slice(None),[]) if depth>=2 else None; instructions.extend(os.path.join(root,n) for n in names if n=="CLAUDE.md" or (n.startswith("AGENTS") and n.endswith(".md")) or n.endswith(".rules"))
 except Exception as exc: errors.append(f"{type(exc).__name__}: {exc}")
 mark("agent_home",not errors and not instructions,errors=errors,instruction_files=instructions,home=home,code_home=code_home)
 forbidden=["/home","/root","/mnt","/media","/srv","/opt","/Users/wade/Documents/MDs_EVAL"]; listed=[]; denied={}
 for path in forbidden:
  try: os.listdir(path); listed.append(path)
  except OSError as exc: denied[path]=type(exc).__name__
 mark("forbidden_paths",not listed,denied=denied,listed=listed); exists=os.path.lexists("/var/run/docker.sock"); mark("docker_socket",not exists,exists=exists); mark("non_root",os.geteuid()!=0,euid=os.geteuid())
 current=os.path.realpath(sys.executable); current_sha=file_sha(current); candidates=[]
 for directory in os.environ.get("PATH","").split(os.pathsep):
  try:
   for name in os.listdir(directory): path=os.path.join(directory,name); candidates.append({"path":path,"realpath":os.path.realpath(path),"sha256":file_sha(os.path.realpath(path))}) if re.fullmatch(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?",name) and os.access(path,os.X_OK) else None
  except Exception as exc: mark("path_scan",False,directory=directory,error=f"{type(exc).__name__}: {exc}")
 mark("interpreter_set",current.startswith("/python/") and (shutil.which("python3") or "").startswith("/python/") and bool(candidates) and all(x["realpath"]==current and x["sha256"]==current_sha for x in candidates),candidates=candidates,current=current); mark("interpreter_pin",platform.python_version()==item["interpreter_pin"],actual=platform.python_version(),expected=item["interpreter_pin"])
def runtime_check(path,image):
 try:
  data=json.load(open(path,encoding="utf-8")); args=data["runtime_args"]; security=data["runtime_security_args"]; policy=data["policy"]; identity=data["identity"]; runtime_hash=sha(json.dumps(security,sort_keys=True,separators=(",",":"))); source,sp=policy_shape(policy["source_argv"]); replay,rp=policy_shape(policy["replay_argv"])
  hashes=policy["source_sha256"]==policy["replay_sha256"]==argv_sha(source)==argv_sha(replay); denial=policy["denial"]; target=policy["socket_target"]; policy_good=source==replay and sp==rp and hashes and isinstance(target,list) and len(target)==2 and isinstance(target[0],str) and isinstance(target[1],int) and policy["bare_connect"] is True and policy["exit_status"]==errno.EPERM and "PermissionError" in denial and any(x in denial for x in ("EPERM","Errno 1","Operation not permitted"))
  current=globals()["identity"](image); identity_good=set(identity)=={"subject","checker"} and identity["subject"]==identity["checker"]==current
  good=all(isinstance(x,list) and x and all(isinstance(y,str) and y for y in x) for x in (args,security)) and data.get("runtime_security_sha256")==runtime_hash and data.get("policy_sha256")==policy["source_sha256"] and policy_good and identity_good and policy.get("source_identity")==policy.get("replay_identity")==current
  mark("runtime_policy_identity",good,identity=identity,policy=policy,runtime_args=args,runtime_security_args=security,runtime_security_sha256=runtime_hash); return runtime_hash,policy["source_sha256"]
 except Exception as exc: mark("runtime_policy_identity",False,error=f"{type(exc).__name__}: {exc}"); return None,None
def main():
 if len(sys.argv)>=2 and sys.argv[1]=="policy-child": return policy_child()
 if len(sys.argv)>=2 and sys.argv[1]=="identity": emit("identity","PASS",**identity(sys.argv[2] if len(sys.argv)>2 else None)); return 0
 default=os.path.join(os.path.dirname(__file__),"contamination-spec.json"); spec_path=sys.argv[4] if len(sys.argv)>4 else os.environ.get("MDSEVAL_CONTAMINATION_SPEC",default); spec,spec_hash=load_spec(spec_path)
 if spec is None or len(sys.argv)<4 or sys.argv[1] not in {"host","container"} or sys.argv[2] not in IDS: emit("summary","BUILD_REJECTED",image_digest=sys.argv[3] if len(sys.argv)>3 else None,spec_sha256=spec_hash,task_id=sys.argv[2] if len(sys.argv)>2 else None); return 2
 mode,task,image=sys.argv[1:4]; workspace=os.path.normpath(os.environ.get("MDSEVAL_WORKSPACE",os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")) if mode=="host" else "/workspace")); item=spec[task]
 mark("invocation",mode=="host" or (workspace=="/workspace" and re.fullmatch(r"sha256:[0-9a-f]{64}",image) is not None),mode=mode,task_id=task,image_digest=image,spec_path=spec_path,workspace=workspace); inspect_targets(item); scan(item,workspace,mode); mount_check(); environment_check(item)
 runtime_path=sys.argv[5] if len(sys.argv)>5 else os.environ.get("MDSEVAL_PROBE_RUNTIME_JSON"); runtime_hash=policy_hash=None
 if mode=="container": runtime_hash,policy_hash=runtime_check(runtime_path,image) if runtime_path else (mark("runtime_policy_identity",False,error="missing runtime JSON") or (None,None))
 status="EXPECTED_RED" if mode=="host" and CONTAM else "ALL_GREEN" if mode=="container" and not BAD and not CONTAM else "CONTROL_FAILED" if mode=="host" else "BUILD_REJECTED"; summary={"check":"summary","status":status,"task_id":task,"spec_sha256":spec_hash,"image_digest":image,"failure_count":len(BAD),"contamination_count":len(CONTAM)}
 summary.update(runtime_security_sha256=runtime_hash,policy_sha256=policy_hash) if mode=="container" else None; print(json.dumps(summary,sort_keys=True,separators=(",",":")),flush=True); return 0 if status in {"EXPECTED_RED","ALL_GREEN"} else 2
if __name__=="__main__": raise SystemExit(main())
