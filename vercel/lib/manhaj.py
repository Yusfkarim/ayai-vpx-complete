"""Global Salafi-manhaj compliance for EVERY chat answer, every model/project.

Always-on base line (cheap, inert for non-religious questions) + extended
ruling line when the question touches Islamic rulings (music, worship,
halal/haram, etc). Scholars of reference: Ibn Baz, Ibn Uthaymeen,
Saleh Al-Fawzan. stdlib only.
"""
try:
    from kb import norm
except Exception:
    import unicodedata as _u

    def norm(s):
        return _u.normalize("NFKC", str(s or "")).strip().lower()

BASE = ("التزام عام في كل إجابة: لا تخالف منهج السلف الصالح كما يقرره كبار "
        "العلماء كابن باز وابن عثيمين وصالح الفوزان.")

EXT = ("مسألة شرعية: اذكر الحكم وفق هؤلاء العلماء باختصار ولا تحل شيئا منها "
       "ولا تقترحه (تحريم الموسيقى والغناء وآلات الطرب والاختلاط والتبرج "
       "والربا والتدخين والشيشة والمسلسلات والأفلام الماجنة والبدع كالاحتفال "
       "بالمولد وأعياد الميلاد) واقترح البديل المباح.")

_RELIG = ["موسيق", "غن", "اغان", "اغني", "اناشيد", "دف", "حلال", "حرام", "فتو", "صلاه",
          "صيام", "صوم", "زكاه", "حج", "عمره", "مسجد", "قران", "حديث",
          "سنه", "بدعه", "شيخ", "حجاب", "نقاب", "لحيه", "اختلاط", "ربا",
          "زنا", "خمر", "تدخين", "شيشه", "اركيله", "قمار", "يانصيب",
          "تمثال", "كلب", "عيد", "مولد", "عاشورا", "تبرج", "مكياج",
          "عطر", "وضو", "تيمم", "اذان", "زواج", "طلاق", "ميراث", "دعاء",
          "استغفار", "عوره", "بنوك", "قرض", "عباده", "تقوى", "ايمان",
          "شرك", "سحر", "ابراج", "رقص", "حفله", "سينما", "شطرنج",
          "halal", "haram", "fatwa", "music", "song", "prayer", "fasting",
          "mosque", "quran", "hijab", "riba", "bidah"]


def relig(text):
    """True if the text touches an Islamic-ruling topic."""
    try:
        n = norm(text)
    except Exception:
        return False
    if not n:
        return False
    return any(r in n for r in _RELIG)


def prompt(text):
    """System line(s) to prepend. Never raises."""
    try:
        if relig(text):
            return BASE + " " + EXT
        return BASE
    except Exception:
        return BASE
