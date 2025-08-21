#!/usr/bin/env python3
"""
Focused test for profession endpoints as requested in the review.
"""
import requests
import json

def test_profession_endpoints():
    base_url = "https://energie-wellbeing.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🩺 Testing Profession Endpoints")
    print("=" * 50)
    
    # Test 1: GET /api/professions
    print("\n1️⃣ Testing GET /api/professions")
    try:
        response = requests.get(f"{api_url}/professions", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ HTTP 200 - Success")
            print(f"   ✅ JSON array with {len(data)} professions")
            
            if len(data) >= 3:
                print(f"   ✅ Count >= 3 professions (found {len(data)})")
            else:
                print(f"   ❌ Expected >= 3, got {len(data)}")
            
            # Check structure of first item
            if data:
                first = data[0]
                required_fields = ['slug', 'label', 'icon', 'order_index', 'is_active']
                missing = [f for f in required_fields if f not in first]
                if not missing:
                    print(f"   ✅ All required fields present: {required_fields}")
                    print(f"   📋 Sample: {first['label']} ({first['slug']}) {first['icon']}")
                else:
                    print(f"   ❌ Missing fields: {missing}")
        else:
            print(f"   ❌ Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: GET /api/professions/infirmier/progression (without user_id)
    print("\n2️⃣ Testing GET /api/professions/infirmier/progression (no user_id)")
    try:
        response = requests.get(f"{api_url}/professions/infirmier/progression", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ HTTP 200 - Success")
            
            required_fields = ['profession_label', 'profession_icon', 'progression_niveau', 'progression_xp']
            missing = [f for f in required_fields if f not in data]
            if not missing:
                print(f"   ✅ All required fields present: {required_fields}")
                
                niveau = data.get('progression_niveau')
                xp = data.get('progression_xp')
                
                if niveau == 1:
                    print(f"   ✅ progression_niveau = 1 (default)")
                else:
                    print(f"   ❌ Expected progression_niveau = 1, got {niveau}")
                
                if 0 <= xp <= 100:
                    print(f"   ✅ progression_xp in range 0-100 (got {xp})")
                else:
                    print(f"   ❌ Expected progression_xp 0-100, got {xp}")
                
                print(f"   📋 Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   ❌ Missing fields: {missing}")
        else:
            print(f"   ❌ Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Create demo user and test with user_id
    print("\n3️⃣ Creating demo user and testing progression with user_id")
    demo_user_id = None
    try:
        # Create demo user
        user_data = {
            "email": "demo@example.com",
            "name": "Utilisateur Demo", 
            "profession_slug": "infirmier"
        }
        response = requests.post(f"{api_url}/users", json=user_data, timeout=10)
        print(f"   Create User Status: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            demo_user_id = user.get('id')
            print(f"   ✅ Demo user created/found: {demo_user_id}")
            
            # Test progression with user_id
            response = requests.get(f"{api_url}/professions/infirmier/progression?user_id={demo_user_id}", timeout=10)
            print(f"   Progression Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ HTTP 200 - Success")
                
                required_fields = ['profession_label', 'profession_icon', 'progression_niveau', 'progression_xp']
                missing = [f for f in required_fields if f not in data]
                if not missing:
                    print(f"   ✅ All required fields present")
                    
                    niveau = data.get('progression_niveau')
                    xp = data.get('progression_xp')
                    
                    if niveau >= 1:
                        print(f"   ✅ progression_niveau >= 1 (got {niveau})")
                    else:
                        print(f"   ❌ Expected progression_niveau >= 1, got {niveau}")
                    
                    if 0 <= xp <= 100:
                        print(f"   ✅ progression_xp in range 0-100 (got {xp})")
                    else:
                        print(f"   ❌ Expected progression_xp 0-100, got {xp}")
                    
                    if data.get('profession_label') and data.get('profession_icon'):
                        print(f"   ✅ profession_label and profession_icon present")
                    else:
                        print(f"   ❌ Missing profession_label or profession_icon")
                    
                    print(f"   📋 Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"   ❌ Missing fields: {missing}")
            else:
                print(f"   ❌ Expected 200, got {response.status_code}")
                print(f"   Error: {response.text}")
        else:
            print(f"   ❌ User creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: GET /api/professions/infirmier/quests
    print("\n4️⃣ Testing GET /api/professions/infirmier/quests")
    try:
        response = requests.get(f"{api_url}/professions/infirmier/quests", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ HTTP 200 - Success")
            print(f"   ✅ JSON array with {len(data)} quests")
            
            if data:
                # Check structure of first quest
                first = data[0]
                required_fields = ['title', 'description', 'points_reward', 'type']
                missing = [f for f in required_fields if f not in first]
                if not missing:
                    print(f"   ✅ All required fields present: {required_fields}")
                    print(f"   📋 Sample quest: {first['title']} ({first['type']}) - {first['points_reward']} pts")
                    print(f"   📋 Full response: {json.dumps(data, indent=2)}")
                else:
                    print(f"   ❌ Missing fields: {missing}")
            else:
                print(f"   ⚠️  No quests found (empty array)")
        else:
            print(f"   ❌ Expected 200, got {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Profession endpoints testing complete!")

if __name__ == "__main__":
    test_profession_endpoints()