import json, os, sys
B = sys.argv[1]
p = f"{B}/05_Plan/episode_log.json"; d = json.load(open(p))
if not any(x.get("ep") == 9 for x in d["done"]):
    cat = d["rotation"][d["next_rotation_index"]]
    d["done"].append({"ep": 9, "cat": cat, "topic": "Black hole"})
    d["series_done"][cat] = d["series_done"].get(cat, 0) + 1
    d["next_ep"] += 1
    d["next_rotation_index"] = (d["next_rotation_index"] + 1) % len(d["rotation"])
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
p = f"{B}/05_Plan/lao_pronunciation.md"; s = open(p).read()
rows = ["| supernova | ຊູເປີໂນວາ | ໃຊ້ແລ້ວ EP.9 |", "| event horizon | ຂອບຟ້າເຫດການ | ໃຊ້ແລ້ວ EP.9 |", "| marble (ລູກແກ້ວ) | ໝາກບີ້ | ໃຊ້ແລ້ວ EP.9 |", "| Gaia BH1 | Gaia BH1 (ໃສ່ການ໌ດ ບໍ່ອ່ານ) | ໃຊ້ແລ້ວ EP.9 |"]
add = [r for r in rows if r.split("|")[1].strip() not in s]
if add:
    anchor = "| Marie Curie | ມາຣີ ກູຣີ | ລໍຖ້າກວດ |"
    s = s.replace(anchor, anchor + "\n" + "\n".join(add)) if anchor in s else s + "\n" + "\n".join(add) + "\n"
    open(p, "w").write(s)
p = f"{B}/05_Plan/playlists.md"; s = open(p).read()
if "EP.9" not in s:
    s = s.replace("- 🚀 ຮູ້ບໍ່? ອາວະກາດ — EP.1, EP.6", "- 🚀 ຮູ້ບໍ່? ອາວະກາດ — EP.1, EP.6, EP.9"); open(p, "w").write(s)
print(json.dumps({k: d[k] for k in ("next_ep", "next_rotation_index", "series_done")}, ensure_ascii=False))
