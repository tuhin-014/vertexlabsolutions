#!/usr/bin/env python3
import jwt, time, json, sys, urllib.request

KEY_ID = "52CR33PAQ7"
ISSUER = "ccb62dc8-92a2-439a-889c-bec3e74503ef"
KEY_PATH = "/Users/clawbot/Downloads/AuthKey_52CR33PAQ7.p8"

with open(KEY_PATH) as f:
    priv = f.read()

tok = jwt.encode(
    {"iss": ISSUER, "iat": int(time.time()), "exp": int(time.time()) + 1200, "aud": "appstoreconnect-v1"},
    priv, algorithm="ES256", headers={"kid": KEY_ID},
)

def api(path):
    req = urllib.request.Request("https://api.appstoreconnect.apple.com" + path,
                                 headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

apps = []
url = "/v1/apps?limit=200&fields[apps]=name,bundleId,sku"
while url:
    d = api(url)
    apps.extend(d["data"])
    nxt = d.get("links", {}).get("next")
    url = nxt.replace("https://api.appstoreconnect.apple.com", "") if nxt else None

print(f"TOTAL APPS: {len(apps)}\n")

rows = []
for a in apps:
    aid = a["id"]
    name = a["attributes"]["name"]
    try:
        v = api(f"/v1/apps/{aid}/appStoreVersions?limit=1&fields[appStoreVersions]=versionString,appStoreState,createdDate")
        if v["data"]:
            va = v["data"][0]["attributes"]
            rows.append((va.get("appStoreState",""), name, va.get("versionString",""), va.get("createdDate",""), aid))
        else:
            rows.append(("(no version)", name, "", "", aid))
    except Exception as e:
        rows.append((f"ERR:{e}", name, "", "", aid))

order = ["IN_REVIEW","WAITING_FOR_REVIEW","PENDING_APPLE_RELEASE","PENDING_DEVELOPER_RELEASE","REJECTED","METADATA_REJECTED","INVALID_BINARY","DEVELOPER_REJECTED","PREPARE_FOR_SUBMISSION","READY_FOR_REVIEW","READY_FOR_SALE"]
def keyf(r):
    s = r[0]
    return (order.index(s) if s in order else 99, r[1])
rows.sort(key=keyf)
for state, name, ver, created, aid in rows:
    print(f"{state:28} | {name[:42]:42} | {ver:8} | {created[:10]} | {aid}")

from collections import Counter
c = Counter(r[0] for r in rows)
print("\n=== STATE COUNTS ===")
for s, n in c.most_common():
    print(f"{n:3}  {s}")
