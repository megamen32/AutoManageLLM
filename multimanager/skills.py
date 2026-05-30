"""Skills operations: master dir, per-program toggles, sync."""
import shutil
from pathlib import Path
from .settings import MASTER_SKILLS, PROGRAMS, expand_path


def scan_master_skills():
    MASTER_SKILLS.mkdir(parents=True, exist_ok=True)
    skills = []
    for d in sorted(MASTER_SKILLS.iterdir()):
        if d.is_dir():
            md = d / "SKILL.md"
            skills.append({"name": d.name, "path": str(d), "has_md": md.exists(),
                           "size": md.stat().st_size if md.exists() else 0})
    return skills


def scan_all_skill_dirs():
    result = {}
    for prog in PROGRAMS:
        sd = expand_path(prog["skills_dir"])
        if sd.exists():
            result[prog["id"]] = [d.name for d in sd.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
        else:
            result[prog["id"]] = []
    from .config import ensure_defaults
    extra = [expand_path(p) for p in ensure_defaults().get("custom_skill_roots", [])]
    for sd in extra:
        if sd.exists():
            result["extra"] = [d.name for d in sd.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    return result


def sync_skill_to_programs(skill_name, program_ids):
    src = MASTER_SKILLS / skill_name
    if not src.exists(): return False, f"Skill {skill_name} not in master"
    results = []
    for pid in program_ids:
        prog = next(p for p in PROGRAMS if p["id"] == pid)
        dst = expand_path(prog["skills_dir"]) / skill_name
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists(): shutil.rmtree(str(dst))
            shutil.copytree(str(src), str(dst))
            results.append(f"{prog['name']}: OK")
        except Exception as e:
            results.append(f"{prog['name']}: {e}")
    return True, "; ".join(results)


def sync_all_skills():
    results = []
    for sk in scan_master_skills():
        ok, msg = sync_skill_to_programs(sk["name"], [p["id"] for p in PROGRAMS])
        results.append(msg)
    return results


def collect_skill_to_master(skill_name, source_program_id):
    prog = next(p for p in PROGRAMS if p["id"] == source_program_id)
    src = expand_path(prog["skills_dir"]) / skill_name
    if not src.exists(): return False, f"Skill not found in {prog['name']}"
    dst = MASTER_SKILLS / skill_name
    MASTER_SKILLS.mkdir(parents=True, exist_ok=True)
    if dst.exists(): shutil.rmtree(str(dst))
    shutil.copytree(str(src), str(dst))
    return True, f"Collected {skill_name} from {prog['name']}"


def delete_skill_from_master(skill_name):
    dst = MASTER_SKILLS / skill_name
    if dst.exists(): shutil.rmtree(str(dst))
    return True
