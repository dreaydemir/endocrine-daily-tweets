from datetime import datetime

THEMES = {
    "monday":     {"theme": "endocrine syndromes", 
                   "hashtags": "#Endocrinology #EndocrineSyndromes #MondaySyndrome"},
    
    "tuesday":    {"theme": "diabetes OR obesity", 
                   "hashtags": "#Endocrinology #Diabetes #Obesity"},
    
    "wednesday":  {"theme": "thyroid disorders", 
                   "hashtags": "#Endocrinology #Thyroid"},
    
    "thursday":   {"theme": "adrenal gland disease (Adrenal Incidentaloma OR Hypercortisolism OR Mild Autonomous Cortisol Secretion OR Pheochromocytoma OR Aldosteronism)", 
                   "hashtags": "#Endocrinology #Adrenal #AdrenalIncidentaloma #Hypercortisolism #MACS #Pheochromocytoma #Aldosteronism"},
    
    "friday":     {"theme": "bone health OR osteoporosis OR parathyroid disorders", 
                   "hashtags": "#Endocrinology #BoneHealth #Osteoporosis"},
    
    "saturday":   {"theme": "artificial intelligence AND machine learning AND endocrinology", 
                   "hashtags": "#Endocrinology #AI #MachineLearning"},
    
    "sunday":     {"theme": "case report AND endocrinology", 
                   "hashtags": "#Endocrinology #CaseReport"},
}

def today_theme():
    weekday = datetime.now().strftime("%A").lower()
    t = THEMES[weekday]
    return t["theme"], t["hashtags"].split()

# ----------------- Test Bloğu -----------------
if __name__ == "__main__":
    theme, hashtags = today_theme()
    print(f"Bugün: {datetime.now().strftime('%A')}")
    print(f"Tema: {theme}")
    print(f"Hashtagler: {hashtags}")

