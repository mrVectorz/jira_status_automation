# Red Hat JIRA Authentication Guide

## 🔍 **Problem Diagnosed**

Your Red Hat JIRA instance (`issues.redhat.com`) is rejecting **ALL** authentication attempts with:
```
403 Forbidden - CAPTCHA_CHALLENGE
x-authentication-denied-reason: CAPTCHA_CHALLENGE; login-url=https://issues.redhat.com/login.jsp
```

This means Red Hat JIRA requires **OAuth authentication** rather than basic API token authentication.

## ✅ **Why Your test.py Works**

Your working test script likely uses one of these methods:
1. **OAuth tokens** instead of API tokens
2. **Session-based authentication** (login via web browser first)
3. **Different JIRA instance** or endpoint
4. **VPN/network access** that bypasses CAPTCHA

## 🔍 **How to Find Out What Works**

Run this command to see what authentication your working script uses:
```bash
grep -i 'oauth\|session\|auth\|token\|login' your_test.py
```

Look for:
- OAuth consumer keys/secrets
- Session cookies
- Different base URLs
- Login flows

## 🛠️ **Solutions**

### Option 1: Use OAuth (Recommended for Red Hat JIRA)

1. **Set up OAuth Application in Red Hat JIRA:**
   ```
   1. Go to https://issues.redhat.com/plugins/servlet/applinks/listApplicationLinks
   2. Create new Application Link
   3. Get Consumer Key and Consumer Secret
   4. Generate Access Tokens
   ```

2. **Update your config.json:**
   ```json
   {
     "jira_oauth": {
       "base_url": "https://issues.redhat.com",
       "consumer_key": "your-oauth-consumer-key",
       "consumer_secret": "your-oauth-consumer-secret", 
       "access_token": "your-oauth-access-token",
       "access_token_secret": "your-oauth-token-secret"
     }
   }
   ```

### Option 2: Copy Your Working Method

1. **Share your working test.py authentication code**
2. **We'll adapt our tool to use the same method**

Example questions:
- Does your test.py import `from jira import JIRA`?
- Does it use OAuth credentials?
- Does it do web login first?

### Option 3: Session-Based Authentication

If your test.py uses session cookies:
1. Login via web browser to https://issues.redhat.com
2. Extract session cookies
3. Use cookies for API requests

## 🧪 **Testing Tools Available**

We've created several debugging tools:

```bash
# Comprehensive authentication testing
./jira_status.sh test-auth

# Red Hat specific testing  
python3 debug_requests.py

# CAPTCHA bypass attempts
python3 bypass_captcha_test.py
```

## 📋 **What We Found**

### ✅ Working (your test.py):
- Successfully authenticates to Red Hat JIRA
- Can access JIRA APIs
- Method unknown (need your help to identify)

### ❌ Not Working (our tool):
- Basic authentication with API tokens → 403 CAPTCHA_CHALLENGE
- All standard authentication methods → 403 CAPTCHA_CHALLENGE
- Python-jira library default methods → 403 CAPTCHA_CHALLENGE

### 🔍 OAuth Endpoints Available:
- `/.well-known/oauth_authorization_server` → 200 ✅
- `/rest/oauth/request-token` → 200 ✅

## 🎯 **Next Steps**

1. **Share your working authentication method:**
   ```bash
   # Show us the authentication part of your working script
   grep -A 10 -B 5 "auth\|JIRA\|oauth" your_test.py
   ```

2. **Try OAuth setup** if you have Red Hat JIRA admin access

3. **Check VPN/network requirements** for Red Hat JIRA access

4. **We'll adapt the tool** once we know your working method

## 🚀 **Once Fixed**

After we solve the authentication, you'll have:
- ✅ Automated bi-weekly status reports
- ✅ JIRA task analysis and summaries  
- ✅ Scheduled report generation
- ✅ Multiple project support
- ✅ Story points tracking
- ✅ Team activity insights

The core functionality is complete - we just need to crack the Red Hat authentication puzzle! 🔐
