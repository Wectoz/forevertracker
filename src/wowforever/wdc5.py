"""Read WoW client tables (.db2, WDC5 format) using the field layouts from WoWDBDefs (github.com/wowdev/WoWDBDefs)."""

import re
import struct
from pathlib import Path


def parse_dbd(defs: Path, table: str, layout_hash: int) -> list[dict]:
    """The fields of `table`, in file order, for the layout the .db2 file declares."""
    text = (defs / f"{table}.dbd").read_text(encoding="utf-8")
    types = {}
    cols, rest = text.split("\n\n", 1) if text.startswith("COLUMNS") else ("", text)
    for line in cols.splitlines()[1:]:
        m = re.match(r"(\w+)(?:<[^>]*>)?\s+(\w+)\??", line.strip())
        if m:
            types[m.group(2)] = m.group(1)
    for block in re.split(r"\n\s*\n", rest):
        if re.search(rf"LAYOUT.*\b{layout_hash:08X}\b", block):
            fields = []
            for line in block.splitlines():
                line = line.split("//")[0].strip()
                if not line or line.startswith(("LAYOUT", "BUILD", "COMMENT")):
                    continue
                m = re.match(r"(?:\$([\w,]+)\$)?(\w+)(?:<(u?)(\d+)>)?(?:\[(\d+)\])?", line)
                ann, name, unsigned, size, count = m.groups()
                ann = set((ann or "").split(","))
                fields.append(dict(name=name, ann=ann, type=types.get(name, "int"), unsigned=unsigned == "u",
                                   size=int(size) if size else 32, count=int(count) if count else 1))
            return fields
    raise KeyError(f"{table}: layout {layout_hash:08X} not in definitions")


def _bits(data: bytes, bit_offset: int, bit_count: int) -> int:
    start = bit_offset >> 3
    chunk = int.from_bytes(data[start:start + ((bit_offset & 7) + bit_count + 7) // 8 + 1], "little")
    return (chunk >> (bit_offset & 7)) & ((1 << bit_count) - 1)


def _fit(v: int, field: dict) -> int:
    """A 32-bit pallet or common value cut to the field's declared width: the bits above it are not part of it."""
    if field["size"] >= 32:
        return v
    v &= (1 << field["size"]) - 1
    return v - (1 << field["size"]) if not field["unsigned"] and v >> (field["size"] - 1) else v


def decode_row(b: bytes, p: int, fields: list[dict], rid: int, hotfix: bool = False) -> tuple[dict, int]:
    """One record whose fields are packed in order with strings inline (an offset-map record or a hotfix), and the
    offset just after it. A hotfix also carries the row's relation (e.g. SpellEffect's SpellID) at the end."""
    row = {}
    for f in fields:
        if "noninline" in f["ann"]:
            continue
        vals = []
        for _ in range(f["count"]):
            if f["type"] in ("string", "locstring"):
                end = b.index(b"\0", p)
                vals.append(b[p:end].decode("utf-8", "replace"))
                p = end + 1
            elif f["type"] == "float":
                vals.append(struct.unpack_from("<f", b, p)[0])
                p += 4
            else:
                n = f["size"] // 8
                vals.append(int.from_bytes(b[p:p + n], "little", signed=not f["unsigned"]))
                p += n
        row[f["name"]] = vals if f["count"] > 1 else vals[0]
    relation = next((f for f in fields if "relation" in f["ann"] and "noninline" in f["ann"]), None)
    if hotfix and relation:
        row[relation["name"]] = struct.unpack_from("<I", b, p)[0]
        p += 4
    row["ID"] = rid
    return row, p


def _read_sparse(b: bytes, sections, fields) -> dict[int, dict]:
    """Offset-map tables: variable-size records, fields packed in order, strings inline."""
    out = {}
    for (tact_key, file_offset, rc, _sts, records_end, id_list_size, rel_size, om_count, copy_count) in sections:
        q = records_end
        ids = struct.unpack_from(f"<{id_list_size // 4}I", b, q)
        q += id_list_size
        copies = [struct.unpack_from("<2I", b, q + 8 * k) for k in range(copy_count)]
        q += 8 * copy_count
        entries = [struct.unpack_from("<IH", b, q + 6 * k) for k in range(om_count)]
        for rid, (o, size) in zip(ids, entries):
            if not size or (tact_key and not any(b[o:o + size])):
                continue
            out[rid] = decode_row(b, o, fields, rid)[0]
        for new_id, src in copies:
            if src in out:
                out[new_id] = dict(out[src], ID=new_id)
    return out


def read(path: Path, table: str, defs: Path) -> dict[int, dict]:
    """Every row of a .db2 file, keyed by row ID."""
    b = Path(path).read_bytes()
    (record_count, field_count, record_size, string_table_size, _table_hash, layout_hash,
     _min_id, _max_id, _locale) = struct.unpack_from("<9I", b, 136)
    flags, id_index = struct.unpack_from("<2H", b, 172)
    (total_field_count, _bitpacked_offset, _lookup_cols, fsi_size, common_size, pallet_size,
     section_count) = struct.unpack_from("<7I", b, 176)
    pos = 204
    sections = []
    for _ in range(section_count):
        sections.append(struct.unpack_from("<Q8I", b, pos))
        pos += 40
    pos += 4 * total_field_count  # field_structure (offsets duplicated in storage info)
    storage = [struct.unpack_from("<2H5I", b, pos + 24 * i) for i in range(fsi_size // 24)]
    pos += fsi_size
    pallet_start = pos
    pos += pallet_size
    common_start = pos
    pos += common_size
    if flags & 1:
        return _read_sparse(b, sections, parse_dbd(defs, table, layout_hash))

    # per-field pallet / common offsets
    pallet_ofs, common_ofs, p, c = [], [], pallet_start, common_start
    for st in storage:
        pallet_ofs.append(p)
        common_ofs.append(c)
        if st[3] in (3, 4):
            p += st[2]
        elif st[3] == 2:
            c += st[2]
    common_maps = []
    for i, st in enumerate(storage):
        m = {}
        if st[3] == 2:
            for k in range(st[2] // 8):
                rid, val = struct.unpack_from("<2I", b, common_ofs[i] + 8 * k)
                m[rid] = val
        common_maps.append(m)

    fields = parse_dbd(defs, table, layout_hash)
    inline = [f for f in fields if "noninline" not in f["ann"]]
    relation = next((f for f in fields if "relation" in f["ann"] and "noninline" in f["ann"]), None)
    id_noninline = next((f for f in fields if "id" in f["ann"] and "noninline" in f["ann"]), None)

    # concatenate records and string tables of all sections, as the string offsets assume
    all_records, all_strings, ids, copies, relations = [], b"", [], [], {}
    for (tact_key, file_offset, rc, sts, _end, id_list_size, rel_size, _om, copy_count) in sections:
        q = file_offset
        recs = [b[q + i * record_size:q + (i + 1) * record_size] for i in range(rc)]
        q += rc * record_size
        all_strings += b[q:q + sts]
        q += sts
        sec_ids = list(struct.unpack_from(f"<{id_list_size // 4}I", b, q)) if id_list_size else []
        q += id_list_size
        for k in range(copy_count):
            copies.append(struct.unpack_from("<2I", b, q + 8 * k))
        q += 8 * copy_count
        if rel_size:
            n = struct.unpack_from("<I", b, q)[0]
            for k in range(n):
                fid, idx = struct.unpack_from("<2I", b, q + 12 + 8 * k)
                relations[len(all_records) + idx] = fid
        encrypted = tact_key != 0 and all(not any(r) for r in recs)
        for i, r in enumerate(recs):
            all_records.append(None if encrypted else r)
            ids.append(sec_ids[i] if sec_ids else None)

    out = {}
    for ri, rec in enumerate(all_records):
        if rec is None:
            continue
        row = {}
        rid = ids[ri]
        for fi, f in enumerate(inline):
            off_bits, size_bits, _add, stype, v1, v2, v3 = storage[fi]
            if stype == 0:
                el = max(size_bits // f["count"], 8) if size_bits else f["size"]
                vals = []
                for k in range(f["count"]):
                    o = off_bits // 8 + k * el // 8
                    raw = rec[o:o + el // 8]
                    if f["type"] in ("string", "locstring"):
                        rel = int.from_bytes(raw, "little", signed=True)
                        so = ri * record_size + o + rel - len(all_records) * record_size
                        end = all_strings.find(b"\0", so)
                        vals.append(all_strings[so:end].decode("utf-8", "replace") if 0 <= so < len(all_strings) else "")
                    elif f["type"] == "float":
                        vals.append(struct.unpack("<f", raw)[0])
                    else:
                        vals.append(int.from_bytes(raw, "little", signed=not f["unsigned"]))
            elif stype in (1, 5):
                v = _bits(rec, off_bits, size_bits)
                if stype == 5 and v >> (size_bits - 1):
                    v -= 1 << size_bits
                vals = [v]
            elif stype == 2:
                vals = [None]  # filled after id known
            elif stype == 3:
                idx = _bits(rec, off_bits, size_bits)
                vals = [struct.unpack_from("<I", b, pallet_ofs[fi] + idx * 4)[0]]
            elif stype == 4:
                idx = _bits(rec, off_bits, size_bits)
                vals = list(struct.unpack_from(f"<{v3}I", b, pallet_ofs[fi] + idx * 4 * v3))
            else:
                raise NotImplementedError(f"storage type {stype}")
            if f["type"] == "float" and stype != 0:  # packed floats come out as raw bits
                vals = [struct.unpack("<f", struct.pack("<I", v & 0xFFFFFFFF))[0] for v in vals]
            elif f["type"] == "int" and stype in (3, 4):
                vals = [_fit(v, f) for v in vals]
            row[f["name"]] = vals if f["count"] > 1 else vals[0]
            if "id" in f["ann"] and rid is None:
                rid = row[f["name"]]
        if rid is None:
            rid = ri
        for fi, f in enumerate(inline):
            if storage[fi][3] == 2:
                v = common_maps[fi].get(rid, storage[fi][4])
                row[f["name"]] = struct.unpack("<f", struct.pack("<I", v))[0] if f["type"] == "float" else _fit(v, f)
        if id_noninline:
            row[id_noninline["name"]] = rid
        if relation:
            row[relation["name"]] = relations.get(ri)
        out[rid] = row
    for new_id, src in copies:
        if src in out:
            out[new_id] = dict(out[src], ID=new_id)
    return out


VALID, REMOVED = 1, 2  # hotfix status; 3 (replaced by a later push) and 4 (not public) are skipped


def table_hashes(path: Path) -> tuple[int, int]:
    """A .db2 file's table hash and layout hash, which hotfixes are matched by."""
    return struct.unpack_from("<2I", Path(path).read_bytes(), 152)


def read_hotfixes(path: Path, tables: dict[int, tuple[str, list[dict]]]) -> tuple[int, dict[str, dict[int, dict | None]]]:
    """The client's hotfix cache (DBCache.bin): its build, and for each table in `tables` (table hash: name, fields)
    the hotfixed rows by ID, None for a removed row. The latest push wins."""
    b = Path(path).read_bytes()
    magic, version, build = struct.unpack_from("<4sII", b, 0)
    if magic != b"XFTH" or version != 9:
        raise ValueError(f"{path}: not a version 9 hotfix cache")
    found: dict[tuple[str, int], tuple[int, dict | None]] = {}
    p = 12 + 32  # header and its 32-byte hash
    while p < len(b):
        _magic, _region, push, _unique, table_hash, rid, size, status = struct.unpack_from("<4siiIIIIB", b, p)
        p += 32
        if table_hash in tables and status in (VALID, REMOVED):
            name, fields = tables[table_hash]
            row = None
            if status == VALID:
                row, end = decode_row(b, p, fields, rid, hotfix=True)
                if end != p + size:
                    raise ValueError(f"{name} hotfix {rid}: {end - p} bytes read, {size} stored; definitions out of date?")
            if found.get((name, rid), (-1, None))[0] <= push:
                found[name, rid] = (push, row)
        p += size
    out: dict[str, dict[int, dict | None]] = {}
    for (name, rid), (_push, row) in found.items():
        out.setdefault(name, {})[rid] = row
    return build, out

