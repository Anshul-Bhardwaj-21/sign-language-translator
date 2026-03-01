# Camera Fix Guide - "Could not start video source"

## 🔍 Problem
Error: "Could not start video source" means your camera is being used by another application.

---

## ✅ Solution Steps

### Step 1: Test Camera First
Open this file in your browser to diagnose the issue:
```
file:///D:/Projects/sign-language-translator/frontend/camera-test.html
```

Or navigate to:
```
http://localhost:3000/camera-test.html
```

This will tell you:
- If camera is detected
- If camera is accessible
- What's blocking it

---

### Step 2: Close Apps Using Camera

**Common apps that block camera:**
- Zoom
- Microsoft Teams
- Skype
- Discord
- OBS Studio
- Any other video call app

**How to check:**
1. Press `Ctrl + Shift + Esc` (Task Manager)
2. Look for these apps in "Processes"
3. Right-click → "End task"

---

### Step 3: Check Windows Camera Settings

1. Press `Windows + I` (Settings)
2. Go to **Privacy & Security** → **Camera**
3. Make sure these are ON:
   - "Camera access"
   - "Let apps access your camera"
   - "Let desktop apps access your camera"

---

### Step 4: Check Browser Settings

**Chrome/Edge:**
```
chrome://settings/content/camera
```
- Set to "Sites can ask to use your camera"
- Check if localhost is blocked

**Firefox:**
```
about:preferences#privacy
```
- Check Camera permissions

---

### Step 5: Restart Browser

1. Close ALL browser windows
2. Open Task Manager (Ctrl + Shift + Esc)
3. End any browser processes
4. Restart browser
5. Go to `http://localhost:3000`

---

### Step 6: Test with Diagnostic Tool

1. Open: `http://localhost:3000/camera-test.html`
2. Click "List Devices" - Should show your camera
3. Click "Test Camera" - Should show video
4. If this works, the main app will work too

---

## 🔧 Advanced Fixes

### Fix 1: Reset Browser Permissions
```
chrome://settings/content/siteDetails?site=http://localhost:3000
```
- Reset all permissions
- Refresh page
- Allow camera again

### Fix 2: Disable Hardware Acceleration
Chrome Settings → System → Turn OFF "Use hardware acceleration"

### Fix 3: Update Camera Drivers
1. Device Manager (Win + X → Device Manager)
2. Cameras → Right-click your camera
3. Update driver

### Fix 4: Check Antivirus
Some antivirus software blocks camera access:
- Temporarily disable antivirus
- Test camera
- Add browser to whitelist

---

## 🎯 Quick Test Commands

Open browser console (F12) and run:

```javascript
// Test 1: Check if camera API exists
console.log('getUserMedia available:', !!navigator.mediaDevices?.getUserMedia);

// Test 2: List devices
navigator.mediaDevices.enumerateDevices()
  .then(devices => console.log('Devices:', devices.filter(d => d.kind === 'videoinput')))
  .catch(err => console.error('Error:', err));

// Test 3: Try to access camera
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    console.log('✅ Camera works!', stream);
    stream.getTracks().forEach(t => t.stop());
  })
  .catch(err => console.error('❌ Camera error:', err.name, err.message));
```

---

## 📱 If Nothing Works

### Option 1: Use Different Browser
- Try Firefox if using Chrome
- Try Edge if using Firefox

### Option 2: Use Phone Camera
- Open app on phone browser
- Phone cameras usually have fewer conflicts

### Option 3: Restart Computer
- Sometimes Windows locks the camera
- Restart fixes it

---

## ✨ After Fix

Once camera works in diagnostic tool:
1. Go back to main app: `http://localhost:3000`
2. Create room
3. In pre-join lobby, click "Turn on camera preview"
4. Allow camera permission
5. Video should appear

---

## 🆘 Still Not Working?

Run this diagnostic and share output:

```cmd
# Check camera in use
powershell "Get-Process | Where-Object {$_.ProcessName -match 'zoom|teams|skype|discord'}"

# Check camera devices
powershell "Get-PnpDevice -Class Camera"
```

Then share the output so I can help further.
