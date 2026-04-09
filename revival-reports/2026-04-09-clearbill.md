# Revival Report: ClearBill - Medical Bill Checker

**Date:** 2026-04-09
**Bundle ID:** com.vertexlabsolutions.clearbill
**Previous Status:** DEVELOPER_REJECTED
**App Store Connect ID:** 6759484929

---

## Issues Found & Fixed

### 1. Privacy Policy URL (Fixed)
- **Before:** `https://tuhin-014.github.io/app-policies/clearbill/privacy-policy.html`
- **After:** `https://vertexlabsolutions.com/privacy`
- **Files affected:**
  - `ClearBill/App/ContentView.swift` (disclaimer view)
  - `ClearBill/Views/Common/DisclaimerView.swift`

### 2. Terms of Use URL (Fixed)
- **Before:** `https://tuhin-014.github.io/app-policies/clearbill/terms-of-service.html`
- **After:** `https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`
- **Files affected:**
  - `ClearBill/App/ContentView.swift` (disclaimer view)
  - `ClearBill/Views/Common/DisclaimerView.swift`

### 3. Build Number Bump
- **Before:** Build 1 (version 1.0)
- **After:** Build 2 (version 1.0)
- **Files affected:**
  - `ClearBill.xcodeproj/project.pbxproj`
  - `ClearBill/Info.plist`

### 4. ITSAppUsesNonExemptEncryption
- Already set to `NO` in Info.plist. No change needed.

### 5. Subscriptions / Product IDs
- No subscription groups configured in ASC. This is a free app with no in-app purchases or paywall. No changes needed.

---

## Build & Upload

- **Archive:** Succeeded (xcodebuild archive, CODE_SIGN_STYLE=Automatic, DEVELOPMENT_TEAM=J58UQ6F38C)
- **Export & Upload:** Succeeded (app-store method, automatic signing, destination=upload)
- **Version:** 1.0 (Build 2)
- **Cleanup:** Archive and export artifacts removed from Desktop.

---

## Status

Build uploaded to App Store Connect. Ready for submission to App Review once processing completes.
