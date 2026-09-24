"""Recovery-books knowledge base: addiction-question detection + gist-backed retrieval.

Privacy: book text lives ONLY in a secret gist (KB_GIST), loaded server-side into
memory, never served raw by any endpoint. Chunks are injected into the model
prompt for treatment-grounded answers. stdlib only.
"""
import json
import math
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request

_GIST = os.environ.get("KB_GIST") or ""
_TOK = os.environ.get("GH_TOKEN") or ""
_KB = {"at": 0.0, "etag": "", "chunks": [], "df": {}, "n": 0}

_DIAC = re.compile(r"[ً-ْٰـ]")
_NORM_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ء": "ا",
    "ؤ": "و", "ئ": "ي", "ة": "ه", "ى": "ي", "ی": "ي", "ي": "ي",
    "ھ": "ه", "ک": "ك", "گ": "ك", "چ": "ج", "پ": "ب", "ژ": "ز",
    "ڕ": "ر", "ڵ": "ل", "ۆ": "و", "ە": "ه", "ێ": "ي",
})


def norm(s):
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = _DIAC.sub("", s)
    s = s.translate(_NORM_MAP)
    s = re.sub(r"[^\w\s]", " ", s, flags=re.U)
    return re.sub(r"\s+", " ", s).strip().lower()


_STOP = {"نصيحه", "نصيح", "سوال",
         "احس", "اشعر", "شعرت", "يحس", "تحس", "حسيت", "احساس", "شعور",
         "في", "من", "على", "الى", "ان", "ما", "لا", "هل", "كيف", "لماذا", "ماذا",
         "هذا", "هذه", "التي", "الذي", "مع", "عن", "كل", "قد", "هو", "هي",
         "كان", "اذا", "او", "ثم", "بين", "بعد", "قبل", "عند", "غير", "اي",
         "the", "a", "an", "is", "are", "to", "of", "and", "how", "what",
         "why", "for", "with", "that", "this", "you", "your"}

_STRONG = ["ادمان", "مدمن", "اباح", "استمنا", "تعاف", "انتكاس", "انتكس",
           "شهوه", "شذوذ", "مثلي", "لواط", "زنا", "مخدر", "تدخين", "كحول",
           "حشيش", "افيون",
           "porn", "masturbat", "fap", "addict", "relaps", "pmo", "nofap",
           "الوده", "بورن", "سيكس", "نهيني", "يالووده", "الووده",
           "modmin", "alaada", "alude"]
_STRONG_PAIRS = [("عاده", "سري"), ("غض", "بصر"), ("افلام", "اباحيه"),
                 ("عادة", "سري"), ("سرعه", "القذف"), ("ضعف", "انتصاب"),
                 ("حس", "ضعف"), ("شعر", "ضعف"),
                 ("ابتعد", "مثير"), ("ابتعاد", "مثير"),
                 ("تجنب", "مثير"), ("اجتناب", "مثير")]
_WEAK = ["جنس", "رغبه", "مشاهده", "صور", "افلام", "عاده", "ذنب", "معصيه",
         "توب", "وسواس", "فراغ", "هروب", "خيال", "دوبامين", "انتصاب",
         "ضعف", "ضعيف", "مثير", "حفز", "حفيز", "محفز",
         "كل مره", "وسخ",
         "احتلام", "خلوه", "نظر",
         "reboot", "urge", "trigger", "fantasy", "withdrawal", "libido",
         "dopamine", "testosterone", "edging"]
_INTENT = ["علاج", "تخلص", "ساعد", "مشكله", "حل", "كيف", "طريقه", "نصيحه",
           "اترك", "ترك", "ابطل", "بطل", "قطع", "حفز", "حفيز",
           "help", "problem", "solution", "how", "advice", "quit", "stop",
           "علاج", "چارەسەر", "چاره"]


def detect(text):
    """True if the text is an addiction/recovery question."""
    n = norm(text)
    if not n:
        return False
    for s in _STRONG:
        if s in n:
            return True
    if "قمار" in n and "اقمار" not in n:
        return True
    words = set(n.split())
    bare = {w[2:] if w.startswith("ال") and len(w) > 4 else w for w in words}

    def _pw(w, a):
        return w == a or w.startswith(a) or w.endswith(a)

    for a, b in _STRONG_PAIRS:
        if any(_pw(w, a) for w in bare) and any(_pw(w, b) for w in bare):
            return True
    hits = [w for w in _WEAK if w in n]
    if len(hits) >= 2:
        return True
    if len(hits) == 1 and hits[0] not in ("كل مره",) and any(w in n for w in _INTENT):
        return True
    return False


_SUF = ("ني", "نا", "ها", "هم", "هن", "كم", "كن", "وه", "ون", "ين",
        "ات", "ان", "ه", "ك", "ي")


def stem(t):
    """Light Arabic stemmer: strip conjunctions/articles/prepositions/suffixes."""
    if len(t) <= 3:
        return t
    if t[0] in ("و", "ف") and len(t) > 4:
        t = t[1:]
    if t.startswith("ال") and len(t) > 5:
        t = t[2:]
    if t[0] in ("ب", "ل", "ك") and len(t) > 3:
        t = t[1:]
    for s in _SUF:
        if t.endswith(s) and len(t) - len(s) >= 3:
            t = t[:-len(s)]
            break
    return t


_EXPAND = {"ابدا": ["خطوه", "تعليمات", "اول"], "رحل": ["بدايه", "خطوه"],
           "نصيح": ["تعليمات", "خطوه"],
           "ضعف": ["ضعيف", "رغبه", "مقاومه", "اراده"],
           "ضعيف": ["ضعف", "رغبه", "مقاومه"],
           "مثير": ["تجنب", "حمايه", "وقايه"],
           "ابتعد": ["يبتعد", "ابتعاد"], "ابتعاد": ["ابتعد", "يبتعد"],
           "تجنب": ["يتجنب", "اجتناب"],
           "تحفز": ["مكاسب", "استمرار", "حافز"],
           "حفز": ["مكاسب", "استمرار", "حافز"],
           "تحفيز": ["مكاسب", "استمرار", "حافز"],
           "اتر": ["ترك", "يترك"], "ترك": ["يترك"],
           "رغب": ["مقاومه", "شهوه"],
           "اسو": ["تعليمات", "خطوه"], "سوي": ["تعليمات", "خطوه"],
           "افعل": ["تعليمات", "خطوه"], "اعمل": ["تعليمات", "خطوه"]}
_EXPAND1 = {"ابدا", "رحل", "نصيح", "اسو", "سوي", "افعل", "اعمل"}


def _ingest(chunks):
    df = {}
    for ch in chunks:
        toks = set()
        for t in norm(ch.get("x", "")).split():
            if len(t) > 2 and t not in _STOP:
                toks.add(t)
                toks.add(stem(t))
        ch["_t"] = toks
        for t in toks:
            df[t] = df.get(t, 0) + 1
    _KB.update(chunks=chunks, df=df, n=len(chunks), at=time.time())


def _fetch():
    if not _GIST or not _TOK:
        return False
    req = urllib.request.Request(
        "https://api.github.com/gists/" + _GIST,
        headers={"Authorization": "Bearer " + _TOK,
                 "Accept": "application/vnd.github+json"})
    if _KB["etag"]:
        req.add_header("If-None-Match", _KB["etag"])
    r = None
    for _a in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=25)
            break
        except urllib.error.HTTPError as e:
            if e.code == 304:
                _KB["at"] = time.time()
                return True
            return False
        except Exception:
            time.sleep(1)
    if r is None:
        return False
    try:
        d = json.loads(r.read())
    except Exception:
        return False
    chunks = []
    for name in sorted(d.get("files", {})):
        if not (name.startswith("kb") and name.endswith(".json")):
            continue
        f = d["files"][name]
        c = f.get("content") or ""
        if f.get("truncated") and f.get("raw_url"):
            try:
                rr = urllib.request.Request(
                    f["raw_url"], headers={"Authorization": "Bearer " + _TOK})
                c = urllib.request.urlopen(rr, timeout=25).read().decode("utf-8", "ignore")
            except Exception:
                continue
        try:
            arr = json.loads(c)
            if isinstance(arr, list):
                chunks.extend(arr)
        except Exception:
            pass
    if not chunks:
        return False
    _ingest(chunks)
    try:
        _KB["etag"] = r.headers.get("ETag", "")
    except Exception:
        pass
    return True


def health_check():
    """True if KB loads (memory or fresh gist fetch). For cron death-alerts."""
    try:
        if _KB["chunks"]:
            return True
        return bool(_fetch())
    except Exception:
        return False


def search(query, top=4, maxc=4200):
    """Return [(book, text)] relevant chunks, or []. Never raises."""
    try:
        if time.time() - _KB["at"] > 600 or not _KB["chunks"]:
            _fetch()
        chunks, df, n = _KB["chunks"], _KB["df"], _KB["n"]
        if not chunks:
            return []
        qn = norm(query)
        qr = [t for t in qn.split() if len(t) > 2 and t not in _STOP]
        groups = []
        for t in qr:
            s = stem(t)
            groups.append([(t, 1.0)] if s == t else [(t, 1.0), (s, 0.5)])
        _seen = set(qr) | {stem(t) for t in qr}
        for t in dict.fromkeys(qr + [stem(t) for t in qr]):
            w1 = 1.0 if t in _EXPAND1 else 0.5
            for v in _EXPAND.get(t, []):
                vs = stem(v)
                if vs in _seen or v in _seen:
                    continue
                _seen.update((v, vs))
                groups.append([(v, w1), (vs, w1 * 0.5)] if vs != v else [(v, w1)])
        if not groups:
            return []
        scored = []
        for ch in chunks:
            toks = ch.get("_t") or set()
            s = 0.0
            rare = 0
            for g in groups:
                best = 0.0
                ridf = 0.0
                for t, w in g:
                    if t in toks:
                        _idf = math.log(1.0 + n / (1.0 + df.get(t, 0)))
                        best = max(best, w * _idf)
                        ridf = max(ridf, _idf)
                if ridf >= 4.0:
                    rare += 1
                s += best
            if s <= 0:
                continue
            x = norm(ch.get("x", ""))[:1200]
            for i in range(len(qr) - 1):
                if qr[i] + " " + qr[i + 1] in x:
                    s += 1.5
            scored.append((rare, s, ch))
        scored.sort(key=lambda z: (z[0], z[1]), reverse=True)
        out, total, per_book = [], 0, {}
        for _, _, ch in scored:
            if len(out) >= top:
                break
            b = str(ch.get("b", ""))
            if per_book.get(b, 0) >= 2:
                continue
            t = str(ch.get("x", ""))
            if total + len(t) > maxc and out:
                break
            out.append((b, t))
            per_book[b] = per_book.get(b, 0) + 1
            total += len(t)
        return out
    except Exception:
        return []


def prompt(hits):
    parts = ["أنت مساعد علاجي متخصص ومتعاطف في مجال التعافي من الإدمان "
             "(بما فيه إدمان الإباحية والعادة السرية والانحرافات الجنسية والمخدرات). "
             "أجب بلغة المستخدم. اجعل المعلومات المرجعية التالية المستخلصة من كتب "
             "التعافي المعتمدة أساس إجابتك الأول ولا تعارضها بمعلومات من خارجها: "
             "ادمجها في إجابتك بأسلوبك الخاص ولا تنسخها حرفياً ولا تذكر أرقام "
             "الصفحات ولا تذكر أن لديك كتباً أو نظاماً داخلياً. كن عملياً: خطوات "
             "واضحة قابلة للتطبيق مع تشجيع نفسي متوازن. إذا اختلفت المعلومات "
             "المرجعية في نقطة ما، ادمجها بحكمة: اذكر التوجيه العملي المشترك أولاً "
             "ثم أشر باختصار لوجود وجهة نظر أخرى دون تشتيت القارئ. هذه التعليمات "
             "العلاجية أولوية قصوى: اتبعها حرفياً حتى لو كان لديك شخصية أو دور "
             "افتراضي آخر. ممنوع تقمّص أي شخصية أو لعب أي دور أو التحدث "
             "كشخص آخر في هذا الرد. إذا كان السؤال "
             "خارج موضوع التعافي تجاهل هذه المعلومات تماماً.\n\nمعلومات مرجعية:"]
    for i, (b, t) in enumerate(hits, 1):
        parts.append("[%d] (من كتاب %s): %s" % (i, b, t))
    return "\n".join(parts)
