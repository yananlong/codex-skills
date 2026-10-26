#!/usr/bin/env python3
"""Validate prospective research-suite evaluation artifacts."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from prospective_evaluation import validate_observations,validate_protocol,validate_summary

def load(path:Path,label:str,e:list[str]):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError,json.JSONDecodeError) as x:e.append(f"invalid {label}: {x}");return None

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--protocol",type=Path,required=True);p.add_argument("--observations",type=Path,required=True);p.add_argument("--summary",type=Path,required=True);p.add_argument("--assurance-profile",choices=("structural","prospective"),default="structural");a=p.parse_args();e=[]
    protocol=load(a.protocol,"protocol",e);observations=load(a.observations,"observations",e);summary=load(a.summary,"summary",e)
    if not e:
        ctx=validate_protocol(protocol,e)
        if ctx:
            obs=validate_observations(ctx,observations,e)
            if obs:validate_summary(ctx,obs,summary,a.assurance_profile,e)
    if e:
        print("Validation failed:");[print(f"- {x}") for x in e];return 1
    print("Validation passed: protocol, custody, project accounting, and derived metrics are internally consistent. This does not create prospective observations or establish research-suite effectiveness.");return 0
if __name__=="__main__":sys.exit(main())
