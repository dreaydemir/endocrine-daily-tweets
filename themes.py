# themes.py
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # Python 3.9+

THEMES = {
    0: ("Endocrine syndromes", ["endocrine syndrome"], ["#Endocrinology", "#Syndrome", "#MondaySyndrome"]),
    1: ("Obesity", ["obesity"], ["#Endocrinology", "#Obesity"]),
    2: ("Thyroid disorders", ["thyroid"], ["#Endocrinology", "#Thyroid"]),
    3: ("Diabetes", ["diabetes"], ["#Endocrinology", "#Diabetes"]),
    4: ("Bone health / Osteoporosis / Parathyroid", ["osteoporosis"], ["#Endocrinology", "#Osteoporosis", "#BoneHealth"]),
    5: ("AI in Endocrinology", ["artificial intelligence", "machine learning"], ["#Endocrinology", "#AI"]),
    6: ("Endocrine case reports", ["case report", "endocrine"], ["#Endocrinology", "#CaseReport"]),
}

def today_theme():
    """
    Bugünün temasını döndürür (label, query_terms, hashtags).
    Önce Europe/Istanbul saat dilimini dener; bulunamazsa sistem saatini kullanır.
    """
    try:
        wd = datetime.now(ZoneInfo("Europe/Istanbul")).weekday()  # Pazartesi=0 ... Pazar=6
    except ZoneInfoNotFoundError:
        wd = datetime.now().weekday()
    return THEMES[wd]
