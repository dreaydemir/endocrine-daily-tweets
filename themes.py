from datetime import datetime

THEMES = {
    "monday":     {"theme": "endocrine syndromes (Polycystic Ovary Syndrome OR PCOS OR Cushing's Syndrome OR Conn's Syndrome OR Metabolic Syndrome OR Insulin Resistance Syndrome OR Syndrome X OR Multiple Endocrine Neoplasia Syndrome OR MEN Syndrome OR Addison's Disease OR Adrenal Insufficiency OR Nelson's Syndrome OR Congenital Adrenal Hyperplasia OR Adrenogenital Syndrome OR Sheehan's Syndrome OR Empty Sella Syndrome OR Kallmann Syndrome OR Pendred Syndrome OR McCune-Albright Syndrome OR Pseudohypoparathyroidism OR Albright's Hereditary Osteodystrophy OR Familial Hypocalciuric Hypercalcemia OR Hyperparathyroidism-Jaw Tumor Syndrome OR Laron Syndrome OR Lipodystrophy Syndrome OR Carney Complex OR Werner Syndrome OR Prader-Willi Syndrome)",
                   "hashtags": "#Endocrinology #EndocrineSyndromes #MondaySyndrome"},
    
    "tuesday":    {"theme": "diabetes OR obesity", 
                   "hashtags": "#Endocrinology #Diabetes #Obesity"},
    
    "wednesday":  {"theme": "thyroid disorders (Thyroid Disease OR Hypothyroidism OR Hyperthyroidism OR Hashimoto's Thyroiditis OR Graves' Disease OR Thyroiditis OR Subacute Thyroiditis OR Postpartum Thyroiditis OR Silent Thyroiditis OR Riedel's Thyroiditis OR Goiter OR Multinodular Goiter OR Toxic Multinodular Goiter OR Toxic Adenoma OR Thyroid Nodule OR Thyroid Cancer OR Papillary Thyroid Carcinoma OR Follicular Thyroid Carcinoma OR Medullary Thyroid Carcinoma OR Anaplastic Thyroid Carcinoma OR Pendred Syndrome OR Congenital Hypothyroidism OR Thyroid Hormone Resistance Syndrome OR Sick Euthyroid Syndrome)", 
                   "hashtags": "#Endocrinology #Thyroid"},
    
    "thursday":   {"theme": "adrenal gland disease (Adrenal Incidentaloma OR Hypercortisolism OR Mild Autonomous Cortisol Secretion OR Pheochromocytoma OR Aldosteronism OR Addison OR Adrenal Insufficiency)", 
                   "hashtags": "#Endocrinology #Adrenal #AdrenalIncidentaloma #Hypercortisolism #MACS #Pheochromocytoma #Aldosteronism"},
    
    "friday":     {"theme": "bone health OR osteoporosis OR parathyroid disorders", 
                   "hashtags": "#Endocrinology #BoneHealth #Osteoporosis"},
    
    "saturday":   {"theme": "artificial intelligence OR machine learning OR deep learning", 
                   "hashtags": "#Endocrinology #AI #MachineLearning #ML #DeepLearning"},
    
    "sunday":     {"theme": "case report", 
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

