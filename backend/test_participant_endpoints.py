"""
Manual test script for participant management endpoints.

This script tests the new participant management endpoints:
- GET /api/meetings/{meeting_id}/participants
- POST /api/meetings/{meeting_id}/participants/{user_id}/mute
- POST /api/meetings/{meeting_id}/participants/{user_id}/remove
- PUT /api/meetings/{meeting_id}/participants/{user_id}/video

Requirements: 15.1, 15.2, 15.3, 15.4, 15.8
"""

import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8002"

def test_participant_management():
    """Test participant management endpoints."""
    
    print("=" * 60)
    print("Testing Participant Management Endpoints")
    print("=" * 60)
    
    # Generate test IDs
    host_id = str(uuid4())
    participant_id = str(uuid4())
    
    # Step 1: Create a meeting
    print("\n1. Creating meeting...")
    meeting_data = {
        "title": "Test Meeting for Participant Management",
        "host_id": host_id,
        "max_participants": 10
    }
    
    response = requests.post(f"{BASE_URL}/api/meetings", json=meeting_data)
    if response.status_code != 201:
        print(f"❌ Failed to create meeting: {response.status_code}")
        print(response.text)
        return
    
    meeting = response.json()
    meeting_id = meeting["id"]
    print(f"✓ Meeting created: {meeting_id}")
    
    # Step 2: Host joins the meeting
    print("\n2. Host joining meeting...")
    join_data = {
        "user_id": host_id,
        "user_name": "Host User"
    }
    
    response = requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/join", json=join_data)
    if response.status_code != 200:
        print(f"❌ Failed to join meeting: {response.status_code}")
        print(response.text)
        return
    
    print(f"✓ Host joined meeting")
    
    # Step 3: Participant joins the meeting
    print("\n3. Participant joining meeting...")
    join_data = {
        "user_id": participant_id,
        "user_name": "Test Participant"
    }
    
    response = requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/join", json=join_data)
    if response.status_code != 200:
        print(f"❌ Failed to join meeting: {response.status_code}")
        print(response.text)
        return
    
    print(f"✓ Participant joined meeting")
    
    # Step 4: Get participants list
    print("\n4. Getting participants list...")
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/participants")
    if response.status_code != 200:
        print(f"❌ Failed to get participants: {response.status_code}")
        print(response.text)
        return
    
    participants = response.json()
    print(f"✓ Retrieved {len(participants)} participants:")
    for p in participants:
        print(f"  - {p['user_id']} (host: {p['is_host']}, audio: {p['audio_enabled']}, video: {p['video_enabled']})")
    
    # Step 5: Mute participant
    print("\n5. Muting participant...")
    mute_data = {
        "host_id": host_id,
        "muted": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/meetings/{meeting_id}/participants/{participant_id}/mute",
        json=mute_data
    )
    if response.status_code != 200:
        print(f"❌ Failed to mute participant: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"✓ Participant muted: audio_enabled={result['audio_enabled']}")
    
    # Step 6: Verify mute status
    print("\n6. Verifying mute status...")
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/participants")
    participants = response.json()
    participant = next((p for p in participants if p['user_id'] == participant_id), None)
    if participant and not participant['audio_enabled']:
        print(f"✓ Mute status verified: audio_enabled={participant['audio_enabled']}")
    else:
        print(f"❌ Mute status not updated correctly")
    
    # Step 7: Disable participant video
    print("\n7. Disabling participant video...")
    video_data = {
        "host_id": host_id,
        "video_enabled": False
    }
    
    response = requests.put(
        f"{BASE_URL}/api/meetings/{meeting_id}/participants/{participant_id}/video",
        json=video_data
    )
    if response.status_code != 200:
        print(f"❌ Failed to disable video: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"✓ Participant video disabled: video_enabled={result['video_enabled']}")
    
    # Step 8: Test authorization (non-host trying to mute)
    print("\n8. Testing authorization (non-host trying to mute)...")
    mute_data = {
        "host_id": participant_id,  # Participant trying to mute
        "muted": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/meetings/{meeting_id}/participants/{host_id}/mute",
        json=mute_data
    )
    if response.status_code == 403:
        print(f"✓ Authorization check passed: non-host cannot mute")
    else:
        print(f"❌ Authorization check failed: expected 403, got {response.status_code}")
    
    # Step 9: Remove participant
    print("\n9. Removing participant...")
    remove_data = {
        "host_id": host_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/meetings/{meeting_id}/participants/{participant_id}/remove",
        json=remove_data
    )
    if response.status_code != 200:
        print(f"❌ Failed to remove participant: {response.status_code}")
        print(response.text)
        return
    
    print(f"✓ Participant removed")
    
    # Step 10: Verify participant was removed
    print("\n10. Verifying participant removal...")
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/participants")
    participants = response.json()
    participant = next((p for p in participants if p['user_id'] == participant_id and p['left_at'] is not None), None)
    if participant:
        print(f"✓ Participant removal verified: left_at={participant['left_at']}")
    else:
        print(f"❌ Participant removal not verified correctly")
    
    # Step 11: Test removing host (should fail)
    print("\n11. Testing host removal protection...")
    remove_data = {
        "host_id": host_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/meetings/{meeting_id}/participants/{host_id}/remove",
        json=remove_data
    )
    if response.status_code == 400:
        print(f"✓ Host removal protection passed: cannot remove host")
    else:
        print(f"❌ Host removal protection failed: expected 400, got {response.status_code}")
    
    # Cleanup: End meeting
    print("\n12. Cleaning up...")
    response = requests.delete(f"{BASE_URL}/api/meetings/{meeting_id}")
    if response.status_code == 200:
        print(f"✓ Meeting ended")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # Check if service is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Meeting service is not healthy")
            print("Please start the service with: python backend/meeting_service.py")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to meeting service")
        print("Please start the service with: python backend/meeting_service.py")
        exit(1)
    
    test_participant_management()
