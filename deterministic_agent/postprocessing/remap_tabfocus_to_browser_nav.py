import os, sys, json, glob, argparse, multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import re

def extract_index(a):
    for k in ("page_index","tab_id","index"):
        v = a.get(k)
        if isinstance(v,int): return v
        try:
            return int(v)
        except: pass
    s = a.get("action_str") or ""
    m = re.search(r"tab_focus\((?:index=)?(\d+)\)", s)
    if m: return int(m.group(1))
    return None

def fix_trajectory_dir(d):
    p = os.path.join(d,"trajectory.json")
    if not os.path.exists(p): return "SKIPPED", None
    try:
        with open(p,"r",encoding="utf-8") as f: traj = json.load(f)
    except: return "FAILED","read_error"
    if not isinstance(traj,dict): return "FAILED","not_dict"
    changed = False
    for k in sorted(traj.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x)):
        step = traj[k]
        act = (step.get("action") or {})
        ao = (act.get("action_output") or {})
        name = ao.get("action_name")
        if name != "tab_focus": continue
        idx = extract_index({**ao.get("action", {}), "action_str": act.get("action_str")})
        if idx is None: continue
        act["action_str"] = f"tab_focus(index={idx})"
        act["action_description"] = f"switch to tab {idx}"
        ao["action_name"] = "browser_nav"
        ao["action"] = {"nav_type":"tab_focus","index":idx}
        step["action"] = act
        changed = True
    if not changed: return "SKIPPED", None
    try:
        with open(p,"w",encoding="utf-8") as f: json.dump(traj,f,indent=2,ensure_ascii=False)
    except Exception as e:
        return "FAILED", str(e)
    return "FIXED", None

def worker(d):
    try:
        return d, *fix_trajectory_dir(d)
    except Exception as e:
        return d, "FAILED", str(e)

def discover(paths):
    out = set()
    for a in paths:
        for p in glob.glob(a):
            if os.path.isdir(p):
                if os.path.exists(os.path.join(p,"trajectory.json")):
                    out.add(os.path.abspath(p))
                else:
                    for e in os.scandir(p):
                        if e.is_dir() and os.path.exists(os.path.join(e.path,"trajectory.json")):
                            out.add(os.path.abspath(e.path))
    return sorted(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--num-workers", type=int, default=multiprocessing.cpu_count())
    args = ap.parse_args()
    dirs = discover(args.paths)
    if not dirs:
        print("No trajectory dirs found.")
        return
    res = {"FIXED":0,"SKIPPED":0,"FAILED":0}
    fails = []
    with ProcessPoolExecutor(max_workers=args.num_workers) as ex:
        futs = [ex.submit(worker,d) for d in dirs]
        for f in tqdm(as_completed(futs), total=len(futs), desc="Fixing", unit="dir"):
            d, status, err = f.result()
            res[status] = res.get(status,0)+1
            if status=="FAILED": fails.append((d,err))
    print("\n--- Summary ---")
    print(f"Total: {len(dirs)}")
    for k in ("FIXED","SKIPPED","FAILED"):
        print(f"{k}: {res.get(k,0)}")
    if fails:
        print("\nFailed:")
        for d,e in fails: print(d, "->", e)

if __name__=="__main__":
    main()
