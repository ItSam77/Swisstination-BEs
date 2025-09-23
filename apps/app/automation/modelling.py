import pandas as pd
import numpy as np
import sys
import os
import joblib
from surprise import SVD, Dataset, Reader
from surprise.model_selection import cross_validate

# Add the parent directory to the path to import supabase_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase

# =============================
# 1) Fetch data dari Supabase
# =============================
def get_users_from_db():
    try:
        if supabase is None:
            raise Exception("Supabase client is not initialized")
        r = supabase.table("custom_users").select("user_id, name").execute()
        return pd.DataFrame(r.data)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return pd.DataFrame()

def get_items_from_db():
    try:
        if supabase is None:
            raise Exception("Supabase client is not initialized")
        r = supabase.table("destinasi").select("destinasi_id, nama_destinasi, kategori_id, deskripsi").execute()
        return pd.DataFrame(r.data)
    except Exception as e:
        print(f"Error fetching items: {e}")
        return pd.DataFrame()

def get_ratings_from_db():
    try:
        if supabase is None:
            raise Exception("Supabase client is not initialized")
        
        # First, get the total count of ratings
        count_result = supabase.table("ratings").select("user_id", count="exact").execute()
        total_ratings = count_result.count if hasattr(count_result, 'count') else 0
        print(f"Total ratings in database: {total_ratings}")
        
        # Fetch all ratings without limit
        all_ratings = []
        page_size = 1000  # Supabase default limit
        offset = 0
        
        while True:
            r = supabase.table("ratings").select("user_id, destinasi_id, rating").range(offset, offset + page_size - 1).execute()
            
            if not r.data:
                break
                
            all_ratings.extend(r.data)
            print(f"Fetched {len(r.data)} ratings (total so far: {len(all_ratings)})")
            
            # If we got less than page_size, we've reached the end
            if len(r.data) < page_size:
                break
                
            offset += page_size
        
        print(f"Successfully fetched all {len(all_ratings)} ratings from database")
        return pd.DataFrame(all_ratings)
        
    except Exception as e:
        print(f"Error fetching ratings: {e}")
        return pd.DataFrame()

def main():
    # Check if supabase is properly configured
    if supabase is None:
        print("❌ Supabase client is not initialized. Please check your environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return
    
    print("✅ Supabase client initialized successfully")
    
    df_users  = get_users_from_db()
    df_items  = get_items_from_db()
    df_ratings = get_ratings_from_db()

    # Check if data was fetched successfully
    if df_users.empty:
        print("❌ No users data fetched")
        return
    if df_items.empty:
        print("❌ No items data fetched")
        return
    if df_ratings.empty:
        print("❌ No ratings data fetched")
        return

    print(f"✅ Data fetched successfully:")
    print(f"   - Users: {len(df_users)}")
    print(f"   - Items: {len(df_items)}")
    print(f"   - Ratings: {len(df_ratings)}")

    # Safety: pastikan kolom ada & tidak kosong
    try:
        assert {"user_id","destinasi_id","rating"} <= set(df_ratings.columns), "Kolom ratings tidak lengkap"
        assert {"destinasi_id","kategori_id"} <= set(df_items.columns), "Kolom destinasi tidak lengkap"
    except AssertionError as e:
        print(f"❌ Data validation error: {e}")
        print(f"Ratings columns: {df_ratings.columns.tolist()}")
        print(f"Items columns: {df_items.columns.tolist()}")
        return

    # Surprise lebih aman kalau raw id berupa string
    df_ratings["user_id"] = df_ratings["user_id"].astype(str)
    df_ratings["destinasi_id"] = df_ratings["destinasi_id"].astype(str)
    df_items["destinasi_id"] = df_items["destinasi_id"].astype(str)
    df_items["kategori_id"] = df_items["kategori_id"].astype(int)

    # =============================
    # 2) Train SVD
    # =============================
    reader = Reader(rating_scale=(1,5))
    data = Dataset.load_from_df(df_ratings[['user_id','destinasi_id','rating']], reader)
    trainset = data.build_full_trainset()

    algo = SVD(n_factors=20, n_epochs=50, random_state=42)
    algo.fit(trainset)

    # =============================
    # Print Metrics
    # =============================
    print("=============================")
    print("Dataset Metrics:")
    print("=============================")
    print(f"Total users: {len(df_users)}")
    print(f"Total items: {len(df_items)}")
    print(f"Total ratings: {len(df_ratings)}")
    print(f"Rating sparsity: {len(df_ratings) / (len(df_users) * len(df_items)) * 100:.2f}%")
    print(f"Average rating: {df_ratings['rating'].mean():.2f}")
    print(f"Rating distribution:")
    print(df_ratings['rating'].value_counts().sort_index())
    print()

    print("Category distribution:")
    print(df_items['kategori_id'].value_counts().sort_index())
    print()

    print("=============================")
    print("Model Performance Metrics:")
    print("=============================")
    # Cross-validation metrics
    cv_results = cross_validate(algo, data, measures=['RMSE', 'MAE'], cv=3, verbose=True)
    print(f"RMSE: {cv_results['test_rmse'].mean():.4f} (+/- {cv_results['test_rmse'].std() * 2:.4f})")
    print(f"MAE: {cv_results['test_mae'].mean():.4f} (+/- {cv_results['test_mae'].std() * 2:.4f})")
    print()

    # Create artifacts directory if it doesn't exist
    os.makedirs("artifacts", exist_ok=True)
    
    payload = {
        "algo": algo,
        "trainset": trainset,
        "items_df": df_items[['destinasi_id', 'kategori_id']].copy(),
        "global_mean": trainset.global_mean,
    }
    joblib.dump(payload, "artifacts/model.pkl")

    print("✅ Model saved to artifacts/model.pkl")

if __name__ == "__main__":
    main()
