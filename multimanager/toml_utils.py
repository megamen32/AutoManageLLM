"""Simple TOML parser/writer — no dependencies."""
import json


def parse_toml_simple(text):
    result = {}; current_section = None; current_sub = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"): continue
        if s.startswith("[[") and s.endswith("]]"):
            key = s[2:-2].strip()
            current_section = key; current_sub = None
            result.setdefault(key, [])
            result[key].append({})
            continue
        if s.startswith("[") and s.endswith("]"):
            key = s[1:-1].strip()
            current_section = key; current_sub = None
            if key not in result: result[key] = {}
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            k = k.strip(); v = v.strip()
            if v.startswith('"') and v.endswith('"'): v = v[1:-1]
            elif v == "true": v = True
            elif v == "false": v = False
            else:
                try: v = int(v)
                except:
                    try: v = float(v)
                    except: pass
            if current_section:
                if isinstance(result.get(current_section), list):
                    result[current_section][-1][k] = v
                else:
                    result[current_section][k] = v
            else:
                result[k] = v
    return result


def write_toml_simple(data, top_level_order=None):
    lines = []; top_done = set()
    order = top_level_order or ["model", "model_provider", "model_reasoning_effort", "personality", "approval_policy", "sandbox_mode", "notify"]

    for k in order:
        if k in data and not isinstance(data[k], dict) and not isinstance(data[k], list):
            lines.append(f'{k} = {_toml_val(data[k])}')
            top_done.add(k)

    for k, v in data.items():
        if k in top_done: continue
        if isinstance(v, dict) and not k.startswith("["):
            lines.append(f"\n[{k}]")
            for sk, sv in v.items():
                if isinstance(sv, dict):
                    lines.append(f"\n[{k}.{sk}]")
                    for ssk, ssv in sv.items():
                        lines.append(f'{ssk} = {_toml_val(ssv)}')
                elif isinstance(sv, list):
                    for item in sv:
                        lines.append(f"\n[[{k}.{sk}]]")
                        if isinstance(item, dict):
                            for ik, iv in item.items(): lines.append(f'{ik} = {_toml_val(iv)}')
                else:
                    lines.append(f'{sk} = {_toml_val(sv)}')
        elif isinstance(v, list):
            for item in v:
                lines.append(f"\n[[{k}]]")
                if isinstance(item, dict):
                    for ik, iv in item.items(): lines.append(f'{ik} = {_toml_val(iv)}')
        elif not isinstance(v, (dict, list)):
            lines.append(f'{k} = {_toml_val(v)}')

    return "\n".join(lines)


def _toml_val(v):
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, str): return f'"{v}"'
    if isinstance(v, (int, float)): return str(v)
    if isinstance(v, list): return json.dumps(v)
    return str(v)
