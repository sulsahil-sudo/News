import json, hashlib, urllib.parse, urllib.request, time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

GOOGLE_NEWS = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

CATEGORIES = {
    "سياسة": "politics",
    "اقتصاد": "economy",
    "علوم": "science",
    "تقنية": "technology",
    "رياضة": "sports",
    "صحة": "health",
    "طبيعة": "climate",
    "عام": "world news",
}

LANGS = [("ar","SA","SA:ar"),("en","US","US:en"),("fr","FR","FR:fr"),
         ("es","ES","ES:es"),("de","DE","DE:de"),("tr","TR","TR:tr")]

URGENT_WORDS = ["عاجل","breaking","urgent","الآن","طارئ"]

def has_arabic(t):
    return any("\u0600" <= c <= "\u06FF" for c in t[:30])

def translate(text):
    if not text: return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q=" + urllib.parse.quote(text[:1500])
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
            return "".join(x[0] for x in data[0] if x[0])
    except Exception:
        return text

def classify(title):
    t = title.lower()
    rules = {
        "سياسة": ["انتخاب","رئيس","حكومة","وزير","برلمان","election","president","government"],
        "اقتصاد": ["اقتصاد","بورصة","دولار","نفط","economy","market","inflation"],
        "علوم": ["علم","دراسة","فضاء","science","study","space"],
        "تقنية": ["تقنية","ذكاء","هاتف","technology","software"],
        "رياضة": ["رياضة","كرة","مباراة","sport","match"],
        "صحة": ["صحة","مرض","وباء","health","disease"],
        "طبيعة": ["مناخ","بيئة","climate","weather"],
    }
    for cat, words in rules.items():
        if any(w in t for w in words): return cat
    return "عام"

def is_urgent(title):
    return any(w.lower() in title.lower() for w in URGENT_WORDS)

def fetch_google_news(q, hl="ar", gl="SA", ceid="SA:ar"):
    url = GOOGLE_NEWS.format(q=urllib.parse.quote(q), hl=hl, gl=gl, ceid=ceid)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            content = r.read()
    except Exception as e:
        print("skip " + hl + ": " + str(e)); return []
    try:
        root = ET.fromstring(content)
    except Exception:
        return []
    out = []
    for item in root.iter("item"):
        title = item.findtext("title","")
        link = item.findtext("link","")
        src = item.findtext("source","")
        if not title or not link: continue
        out.append({"title": title, "link": link, "source": src})
    return out

def main():
    seen = {}
    for cat_ar, q in CATEGORIES.items():
        for lang, country, ceid in LANGS:
            items = fetch_google_news(q, hl=lang, gl=country, ceid=ceid)
            for it in items[:12]:
                uid = hashlib.md5(it["link"].encode()).hexdigest()
                if uid in seen: continue
                title_ar = it["title"] if has_arabic(it["title"]) else translate(it["title"])
                seen[uid] = {
                    "id": uid,
                    "title": it["title"],
                    "title_ar": title_ar,
                    "url": it["link"],
                    "source": it["source"],
                    "category": classify(title_ar),
                    "is_urgent": is_urgent(title_ar),
                    "collected": datetime.now(timezone.utc).isoformat(),
                }
            time.sleep(0.3)
    items = sorted(seen.values(), key=lambda x: x["collected"], reverse=True)[:600]
    with open("news.json","w",encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(),
                   "count": len(items), "articles": items},
                  f, ensure_ascii=False, indent=2)
    print("Collected " + str(len(items)) + " articles")

if __name__ == "__main__":
    main()
