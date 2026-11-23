"""Read the pivot cache of an .xlsx file (zip + XML, no openpyxl).

Arbetsförmedlingen publishes its county and municipality statistics as pivot tables: the visible
sheets show only the national total, while the full microdata-like table (one record per month x
county x municipality x sex x age group ...) sits in xl/pivotCache/pivotCacheRecords<n>.xml.

`read_pivot_cache(path, n)` returns that table as a DataFrame: one column per cache field.
Fields with shared items (categories) are decoded to their labels; numeric fields come back as float.
The records file can be >100 MB, so it is parsed incrementally (iterparse).
"""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _item_value(el):
    tag = el.tag.removeprefix(M)
    v = el.get("v")
    if tag == "n":
        return float(v)
    if tag in ("m",):
        return None
    return v


def cache_fields(path: Path, n: int) -> list[tuple[str, list]]:
    """(name, shared items) per cache field of pivot cache definition `n`."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read(f"xl/pivotCache/pivotCacheDefinition{n}.xml"))
    out = []
    for f in root.iter(f"{M}cacheField"):
        si = f.find(f"{M}sharedItems")
        out.append((f.get("name"), [_item_value(i) for i in si] if si is not None else []))
    return out


def read_pivot_cache(path: Path, n: int, fields: list[str] | None = None) -> pd.DataFrame:
    """The records of pivot cache `n` as a DataFrame (optionally only `fields`)."""
    defs = cache_fields(path, n)
    names = [d[0] for d in defs]
    keep = [i for i, nm in enumerate(names) if fields is None or nm in fields]
    cols: dict[int, list] = {i: [] for i in keep}
    with zipfile.ZipFile(path) as z, z.open(f"xl/pivotCache/pivotCacheRecords{n}.xml") as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag != f"{M}r":
                continue
            for i, c in enumerate(el):
                if i not in cols:
                    continue
                tag = c.tag.removeprefix(M)
                if tag == "x":
                    cols[i].append(defs[i][1][int(c.get("v"))])
                else:
                    cols[i].append(_item_value(c))
            el.clear()
    return pd.DataFrame({names[i]: cols[i] for i in keep})
