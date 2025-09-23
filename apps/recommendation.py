# recommendation.py
import numpy as np
import pandas as pd
import joblib

ARTIFACTS_PATH = "artifacts/model.pkl"

# ===== Load artifacts sekali di import =====
try:
    _pack = joblib.load(ARTIFACTS_PATH)
    algo = _pack["algo"]
    trainset = _pack["trainset"]
    df_items = _pack["items_df"]
    GLOBAL_MEAN = _pack.get("global_mean", trainset.global_mean)
    
    # Debug info about loaded data
    print(f"[DEBUG] Loaded model artifacts:")
    print(f"[DEBUG] - df_items shape: {df_items.shape}")
    print(f"[DEBUG] - Total destinations in model: {len(df_items)}")
    print(f"[DEBUG] - Available destination IDs: {len(df_items['destinasi_id'].unique())} unique IDs")
    print(f"[DEBUG] - Categories in model: {sorted(df_items['kategori_id'].unique())}")
    ML_MODEL_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Could not load ML model: {e}")
    print("[WARNING] Will use database fallback for all recommendations")
    algo = None
    trainset = None
    df_items = None
    GLOBAL_MEAN = 3.0  # Default rating
    ML_MODEL_AVAILABLE = False

# Kamu bisa tarik df_ratings terbaru dari DB saat runtime jika mau filter "sudah dirating"
# Di sini disediakan hook opsional:
def fetch_latest_ratings():
    # contoh no-op: return DataFrame kosong; di BE nyata ambil dari DB
    return pd.DataFrame(columns=["user_id","destinasi_id","rating"])

df_ratings = fetch_latest_ratings()

# ===== Utilities =====
def known_item(raw_iid: str) -> bool:
    # apakah item pernah dilihat saat training
    if not ML_MODEL_AVAILABLE or trainset is None:
        return False
    return raw_iid in trainset._raw2inner_id_items

def _candidates(restrict_cats=None):
    """
    Get candidate destination IDs, preferring fresh database data over ML model data.
    This ensures we always have the most up-to-date destination list.
    """
    try:
        # Always try to get fresh data from database first
        from supabase_client import supabase
        
        if supabase is not None:
            if restrict_cats is not None:
                result = supabase.table("destinasi").select("destinasi_id").in_("kategori_id", restrict_cats).execute()
            else:
                result = supabase.table("destinasi").select("destinasi_id").execute()
            
            if result.data:
                candidates = [str(dest["destinasi_id"]) for dest in result.data]
                print(f"[DEBUG] _candidates from database: found {len(candidates)} candidates (restrict_cats={restrict_cats})")
                return candidates
    except Exception as e:
        print(f"[DEBUG] _candidates: Error fetching from database: {e}, falling back to model data")
    
    # Fallback to ML model data if database is unavailable
    if not ML_MODEL_AVAILABLE or df_items is None:
        print(f"[DEBUG] _candidates: ML model not available, returning empty list")
        return []
    
    if restrict_cats is not None:
        candidates = df_items.loc[df_items["kategori_id"].isin(restrict_cats), "destinasi_id"].astype(str).tolist()
        print(f"[DEBUG] _candidates from model with restrict_cats {restrict_cats}: found {len(candidates)} candidates")
        return candidates
    candidates = df_items["destinasi_id"].astype(str).tolist()
    print(f"[DEBUG] _candidates from model without restriction: found {len(candidates)} total candidates")
    return candidates

def get_all_items_fallback_from_db(restrict_cats=None, n=10):
    """
    Enhanced fallback function that fetches all destinations directly from the database.
    This ensures we get all current destinations, not just those in the ML model.
    """
    try:
        # Import here to avoid circular imports
        from supabase_client import supabase
        
        if supabase is None:
            print("[DEBUG] Supabase not available, falling back to model data")
            return get_all_items_fallback(restrict_cats, n)
        
        # Fetch all destinations from database
        if restrict_cats is not None:
            result = supabase.table("destinasi").select("destinasi_id, kategori_id").in_("kategori_id", restrict_cats).execute()
        else:
            result = supabase.table("destinasi").select("destinasi_id, kategori_id").execute()
        
        if not result.data:
            print("[DEBUG] No destinations found in database, falling back to model data")
            return get_all_items_fallback(restrict_cats, n)
        
        # Create scored items from database results
        scored_items = []
        for i, dest in enumerate(result.data):
            dest_id = str(dest["destinasi_id"])
            # Simple scoring: descending by order, with some randomness
            basic_score = 10.0 - (i * 0.05) if i < 200 else 1.0
            scored_items.append((dest_id, basic_score))
        
        # Sort by score
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[DEBUG] get_all_items_fallback_from_db: fetched {len(scored_items)} destinations from DB")
        
        # Return all items if n is large, otherwise return requested count
        result_items = scored_items if n >= 1000 else scored_items[:n]
        print(f"[DEBUG] get_all_items_fallback_from_db: returning {len(result_items)} items")
        return result_items
        
    except Exception as e:
        print(f"[DEBUG] Error in get_all_items_fallback_from_db: {e}")
        print("[DEBUG] Falling back to model data")
        return get_all_items_fallback(restrict_cats, n)

def get_all_items_fallback(restrict_cats=None, n=10):
    """
    Original fallback function that uses ML model data.
    """
    candidates = _candidates(restrict_cats)
    print(f"[DEBUG] get_all_items_fallback: processing {len(candidates)} candidates from model, n={n}")
    
    # Assign a basic score (could be based on popularity, alphabetical, etc.)
    # For now, we'll use a simple descending score based on destination_id
    scored_items = []
    for i, iid in enumerate(candidates):
        # Simple scoring: higher score for lower index (you could improve this)
        basic_score = 10.0 - (i * 0.1) if i < 100 else 1.0
        scored_items.append((iid, basic_score))
    
    # Sort by score (already sorted by index, but keeping it explicit)
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    # If n is very large (1000 or more), return all items
    result = scored_items if n >= 1000 else scored_items[:n]
    print(f"[DEBUG] get_all_items_fallback: returning {len(result)} items from model")
    return result

# ===== User lama =====
def topn_for_user(user_id: str, n=10, restrict_cats=None):
    user_id = str(user_id)
    taken = set(df_ratings.loc[df_ratings["user_id"]==user_id, "destinasi_id"].astype(str))
    preds = []
    for iid in _candidates(restrict_cats):
        if iid in taken or not known_item(iid):
            continue
        # Surprise bisa pakai raw id langsung
        est = algo.predict(user_id, iid).est
        preds.append((iid, float(est)))
    preds.sort(key=lambda x: x[1], reverse=True)
    # If n is very large (1000 or more), return all predictions
    return preds if n >= 1000 else preds[:n]

# ===== Cold-start: pseudo user dari kategori =====
def pseudo_user_vector_from_categories(selected_cat_ids: list[int]):
    qvecs = []
    cand_items = df_items.loc[df_items["kategori_id"].isin(selected_cat_ids), "destinasi_id"].astype(str).tolist()
    for iid in cand_items:
        if known_item(iid):
            ii = trainset.to_inner_iid(iid)
            qvecs.append(algo.qi[ii])   # latent vector item
    if not qvecs:
        return None
    return np.mean(np.stack(qvecs, axis=0), axis=0)

def score_items_for_pseudo_user(pu_vec, exclude=set(), restrict_cats=None, n=10):
    scored = []
    for iid in _candidates(restrict_cats):
        if iid in exclude or not known_item(iid):
            continue
        ii = trainset.to_inner_iid(iid)
        qi = algo.qi[ii]
        bi = algo.bi[ii]
        score = GLOBAL_MEAN + bi + float(np.dot(qi, pu_vec))  # bu=0 untuk user baru
        scored.append((iid, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    # If n is very large (1000 or more), return all scored items
    return scored if n >= 1000 else scored[:n]

# ===== Wrapper satu pintu =====
def recommend(user_id: str | None, selected_cat_ids: list[int] | None, n=10, k_min_interactions=3):
    """
    - Jika user punya >=k interaksi → pakai topn_for_user
    - Jika belum → pakai pseudo-user vector dari kategori (cold-start)
    - Fallback populer per kategori jika tak ada vektor pseudo yang valid
    """
    print(f"[DEBUG] recommend called with user_id={user_id}, selected_cat_ids={selected_cat_ids}, n={n}")
    
    # If ML model is not available, use database fallback directly
    if not ML_MODEL_AVAILABLE:
        print(f"[DEBUG] ML model not available, using database fallback directly")
        return get_all_items_fallback_from_db(restrict_cats=selected_cat_ids, n=n)
    
    # hitung interaksi user (pakai df_ratings yang ideally ditarik dari DB terbaru)
    if user_id is not None:
        user_id = str(user_id)
        n_inter = (df_ratings["user_id"].astype(str) == user_id).sum()
        print(f"[DEBUG] User {user_id} has {n_inter} interactions")
        if n_inter >= k_min_interactions:
            print(f"[DEBUG] Using topn_for_user for user {user_id}")
            return topn_for_user(user_id, n=n, restrict_cats=selected_cat_ids)

    # cold-start
    if selected_cat_ids:
        print(f"[DEBUG] Trying cold-start for categories {selected_cat_ids}")
        pu = pseudo_user_vector_from_categories(selected_cat_ids)
        if pu is not None:
            print(f"[DEBUG] Using pseudo-user vector for cold-start")
            return score_items_for_pseudo_user(pu, restrict_cats=selected_cat_ids, n=n)
        else:
            print(f"[DEBUG] Pseudo-user vector is None, falling back")

    # fallback: return all destinations with basic scoring from database
    # This ensures users always see all available destinations
    print(f"[DEBUG] Using fallback recommendations from database")
    return get_all_items_fallback_from_db(restrict_cats=selected_cat_ids, n=n)

# ======= Contoh pemakaian langsung (opsional) =======
if __name__ == "__main__":
    # Contoh: user baru pilih kategori [3,5,6]
    cats = [3,5,6,1]
    print("Cold-start:", recommend(user_id=None, selected_cat_ids=cats, n=5))

    # Contoh: user lama (ganti '123' sesuai data di DB & pastikan df_ratings diisi dari DB)
    print("User lama:", recommend(user_id="123", selected_cat_ids=None, n=5))
