# 🔥 Firebase Integration Guide

## Current Status
✅ Firebase structure ready
✅ Configuration template created
✅ Auth methods defined
✅ Firestore methods defined
⏳ Waiting for your Firebase keys

## How to Integrate Firebase

### Step 1: Create Firebase Project
1. Go to https://console.firebase.google.com
2. Click "Add project"
3. Enter project name (e.g., "video-call-app")
4. Disable Google Analytics (optional)
5. Click "Create project"

### Step 2: Enable Authentication
1. In Firebase Console, go to "Authentication"
2. Click "Get started"
3. Enable "Email/Password" sign-in method
4. Click "Save"

### Step 3: Enable Firestore Database
1. In Firebase Console, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select location (closest to your users)
5. Click "Enable"

### Step 4: Get Configuration
1. In Firebase Console, go to Project Settings (gear icon)
2. Scroll down to "Your apps"
3. Click "Web" icon (</>) to add web app
4. Register app with nickname (e.g., "video-call-web")
5. Copy the configuration object

### Step 5: Add to .env File
Create `frontend/.env` file:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456

# Backend API
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Step 6: Install Firebase SDK
```bash
cd frontend
npm install firebase
```

### Step 7: Uncomment Firebase Code
In `frontend/src/services/firebase.ts`, uncomment:
```typescript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
```

### Step 8: Update AuthContext
In `frontend/src/contexts/AuthContext.tsx`, replace mock auth with Firebase:

```typescript
import { firebaseAuth } from '../services/firebase';

const login = async (email: string, password: string): Promise<void> => {
  const result = await firebaseAuth.signIn(email, password);
  // Handle result
};

const signup = async (name: string, email: string, password: string): Promise<void> => {
  const result = await firebaseAuth.signUp(email, password, name);
  // Handle result
};
```

### Step 9: Test Firebase
1. Restart dev server: `npm run dev`
2. Try signing up with a new account
3. Check Firebase Console → Authentication → Users
4. You should see the new user!

## Firebase Features to Implement

### Authentication
- [x] Structure ready
- [ ] Sign up with email/password
- [ ] Sign in with email/password
- [ ] Sign out
- [ ] Password reset
- [ ] Email verification
- [ ] Google sign-in (optional)

### Firestore Database
- [x] Structure ready
- [ ] Store user profiles
- [ ] Store meeting data
- [ ] Store meeting history
- [ ] Store chat messages
- [ ] Real-time updates

### Firestore Collections Structure
```
users/
  {userId}/
    - name: string
    - email: string
    - avatar: string
    - createdAt: timestamp
    - stats: object

meetings/
  {meetingId}/
    - code: string
    - hostId: string
    - hostName: string
    - participants: array
    - createdAt: timestamp
    - status: string
    - messages: subcollection

messages/
  {messageId}/
    - senderId: string
    - senderName: string
    - text: string
    - timestamp: timestamp
```

### Real-time Features
- [ ] Live participant updates
- [ ] Real-time chat
- [ ] Meeting status updates
- [ ] Presence detection

## Security Rules

### Firestore Rules (for production)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId;
    }
    
    // Meetings
    match /meetings/{meetingId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth.uid == resource.data.hostId;
      allow delete: if request.auth.uid == resource.data.hostId;
    }
    
    // Messages
    match /meetings/{meetingId}/messages/{messageId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
    }
  }
}
```

### Authentication Rules
```javascript
// In Firebase Console → Authentication → Settings
- Email enumeration protection: Enabled
- Password policy: Minimum 8 characters
- Multi-factor authentication: Optional
```

## Current Implementation

### Without Firebase (Demo Mode)
- Uses localStorage for auth
- Uses demo.json for data
- No real-time updates
- No persistence across devices

### With Firebase (Production Mode)
- Real authentication
- Cloud database
- Real-time updates
- Multi-device sync
- Secure and scalable

## Testing Firebase

### Test Authentication
```bash
# Sign up
Email: test@example.com
Password: Test@123

# Check Firebase Console
Authentication → Users → Should see new user
```

### Test Firestore
```bash
# Create meeting
Click "Create New Meeting"

# Check Firebase Console
Firestore Database → meetings → Should see new document
```

## Troubleshooting

### Firebase not working?
1. Check .env file exists and has correct values
2. Restart dev server after adding .env
3. Check browser console for errors
4. Verify Firebase project is active
5. Check Firestore rules allow access

### Authentication errors?
1. Verify Email/Password is enabled in Firebase Console
2. Check password meets requirements (8+ chars)
3. Clear browser cache and try again

### Firestore errors?
1. Check Firestore is enabled in Firebase Console
2. Verify rules allow read/write access
3. Check network tab for API errors

## Next Steps

1. **Add Firebase keys to .env**
2. **Install Firebase SDK**: `npm install firebase`
3. **Uncomment Firebase code** in firebase.ts
4. **Update AuthContext** to use Firebase
5. **Test authentication**
6. **Implement Firestore** for meetings
7. **Add real-time updates**
8. **Deploy to production**

## Benefits of Firebase

✅ **Authentication**: Secure user management
✅ **Database**: Scalable cloud storage
✅ **Real-time**: Live updates across devices
✅ **Security**: Built-in security rules
✅ **Hosting**: Free hosting for frontend
✅ **Analytics**: User behavior tracking
✅ **Free Tier**: Generous free usage limits

## Cost Estimate

### Free Tier (Spark Plan)
- Authentication: 50,000 users/month
- Firestore: 1GB storage, 50K reads/day
- Hosting: 10GB storage, 360MB/day transfer
- **Perfect for development and small apps!**

### Paid Tier (Blaze Plan)
- Pay as you go
- ~$0.06 per 100K reads
- ~$0.18 per 100K writes
- **Only pay for what you use**

---

**Ready to integrate? Just add your Firebase keys to .env and follow the steps above!** 🚀
