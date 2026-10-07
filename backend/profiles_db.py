import json
import os
from typing import List, Optional

PROFILES_FILE = 'backend/profiles.json'

def load_profiles() -> List[dict]:
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_profiles(profiles: List[dict]):
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def get_profile(profile_id: str) -> Optional[dict]:
    for p in load_profiles():
        if p.get('id') == profile_id:
            return p
    return None

def upsert_profile(profile: dict):
    profiles = load_profiles()
    for i, p in enumerate(profiles):
        if p.get('id') == profile['id']:
            profiles[i] = profile
            save_profiles(profiles)
            return
    profiles.append(profile)
    save_profiles(profiles)

def delete_profile(profile_id: str):
    profiles = load_profiles()
    profiles = [p for p in profiles if p.get('id') != profile_id]
    save_profiles(profiles)
