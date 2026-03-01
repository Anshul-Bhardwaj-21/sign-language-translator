# Firebase Setup Guide

This guide walks through setting up Firebase for the Sign Language Accessibility Video Call Application. Firebase is **optional** - the app works fully offline, but Firebase enables multi-user sync, caption history, and incremental learning across devices.

## Why Firebase?

- **Firestore**: Real-time caption sync across call participants
- **Storage**: Model artifact distribution and user correction datasets
- **Authentication** (future): User accounts and preferences
- **Free Tier**: Generous limits suitable for development and small deployments

## Prerequisites

- Google account
- Python 3.10+
- Project already set up locally

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name: `sign-language-accessibility` (or your choice)
4. Disable Google Analytics (optional for this project)
5. Click "Create project"

## Step 2: Enable Firestore Database

1. In Firebase Console, click "Firestore Database" in left sidebar
2. Click "Create database"
3. Select "Start in test mode" (we'll secure it later)
4. Choose a location close to your users (e.g., `us-central1`)
5. Click "Enable"

### Firestore Security Rules (Production)

Once testing is complete, update Firestore rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Captions collection - read/write for authenticated users
    match /captions/{captionId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    
    // Corrections collection - write for authenticated users
    match /corrections/{correctionId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    
    // Sessions collection - read/write for session participants
    match /sessions/{sessionId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

## Step 3: Enable Firebase Storage

1. Click "Storage" in left sidebar
2. Click "Get started"
3. Accept default security rules for now
4. Choose same location as Firestore
5. Click "Done"

### Storage Security Rules (Production)

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Model artifacts - read for all, write for admin only
    match /models/{modelFile} {
      allow read: if true;
      allow write: if request.auth != null && request.auth.token.admin == true;
    }
    
    // User corrections - write for authenticated users
    match /corrections/{userId}/{correctionFile} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## Step 4: Generate Service Account Credentials

1. Click gear icon (⚙️) next to "Project Overview"
2. Click "Project settings"
3. Go to "Service accounts" tab
4. Click "Generate new private key"
5. Click "Generate key" in confirmation dialog
6. Save the JSON file as `firebase-credentials.json`

## Step 5: Configure Application

1. Move `firebase-credentials.json` to your project:
   ```bash
   mkdir -p configs
   mv ~/Downloads/firebase-credentials.json configs/firebase-credentials.json
   ```

2. Update `configs/config.yaml`:
   ```yaml
   firebase:
     enabled: true
     credentials_path: "configs/firebase-credentials.json"
     project_id: "your-project-id"  # From Firebase Console
     storage_bucket: "your-project-id.appspot.com"
     collections:
       captions: "captions"
       corrections: "corrections"
       sessions: "sessions"
   ```

3. Add to `.gitignore`:
   ```
   configs/firebase-credentials.json
   ```

## Step 6: Initialize Firestore Collections

Run the initialization script:

```bash
python backend/firebase_integration.py --init
```

This creates the required collections and indexes.

## Step 7: Test Connection

```bash
python -c "from backend.firebase_integration import FirebaseClient; client = FirebaseClient(); print('Connected:', client.is_connected())"
```

Expected output: `Connected: True`

## Usage in Application

### Storing Captions

```python
from backend.firebase_integration import FirebaseClient

client = FirebaseClient()
client.store_caption(
    session_id="session_123",
    user_id="user_456",
    text="Hello world",
    timestamp=time.time()
)
```

### Storing Corrections

```python
client.store_correction(
    user_id="user_456",
    original_text="HELO",
    corrected_text="HELLO",
    landmark_sequence=landmarks,
    timestamp=time.time()
)
```

### Retrieving Session Captions

```python
captions = client.get_session_captions(
    session_id="session_123",
    limit=50
)
```

## Free Tier Limits

Firebase Free (Spark) Plan includes:

- **Firestore**:
  - 1 GiB storage
  - 50K reads/day
  - 20K writes/day
  - 20K deletes/day

- **Storage**:
  - 5 GB storage
  - 1 GB/day downloads
  - 20K uploads/day

- **Bandwidth**:
  - 10 GB/month

### Optimization Tips

1. **Batch Writes**: Group multiple captions into single write
2. **Local Caching**: Cache recent captions locally
3. **Lazy Sync**: Sync only when needed, not every frame
4. **Compression**: Compress landmark sequences before storage
5. **TTL**: Auto-delete old captions after 30 days

## Monitoring Usage

1. Go to Firebase Console
2. Click "Usage and billing"
3. Monitor daily usage against limits
4. Set up budget alerts

## Troubleshooting

### Error: "Permission Denied"

- Check Firestore security rules
- Verify service account has correct permissions
- Ensure `firebase-credentials.json` is valid

### Error: "Project Not Found"

- Verify `project_id` in `config.yaml` matches Firebase Console
- Check credentials file is for correct project

### Error: "Quota Exceeded"

- Check usage in Firebase Console
- Implement rate limiting
- Consider upgrading to Blaze (pay-as-you-go) plan

### Slow Performance

- Choose Firestore location close to users
- Use indexes for common queries
- Implement local caching
- Batch operations

## Local Development Without Firebase

The app works fully without Firebase:

```yaml
firebase:
  enabled: false
```

All features work locally:
- Captions stored in session state
- Corrections saved to local files
- No network dependency

## Production Deployment

For production:

1. **Enable Authentication**:
   - Set up Firebase Authentication
   - Require auth for all operations
   - Implement user roles

2. **Secure Rules**:
   - Update Firestore and Storage rules
   - Implement row-level security
   - Validate all inputs

3. **Upgrade Plan**:
   - Consider Blaze plan for production
   - Set budget alerts
   - Monitor usage

4. **Backup**:
   - Enable automated backups
   - Export data regularly
   - Test restore procedures

5. **Monitoring**:
   - Set up Firebase Performance Monitoring
   - Enable Crashlytics
   - Configure alerts

## Alternative: Self-Hosted Backend

If you prefer not to use Firebase:

1. Use the FastAPI backend (`backend/server.py`)
2. Set up PostgreSQL or MongoDB
3. Deploy on your own infrastructure
4. Update `backend/storage.py` for your database

## Support

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Pricing](https://firebase.google.com/pricing)
- [Firebase Support](https://firebase.google.com/support)

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-14
