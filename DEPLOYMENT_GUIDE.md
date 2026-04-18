# 🚢 MAIC Deployment Guide
## Maritime Agency & Identity Classifier — Free Deployment on Streamlit Community Cloud

---

## What You're Deploying

A Streamlit web app that:
- Extracts YouTube transcripts (zero API cost)
- Wraps them in a 4-lens Occupational Science qualitative analysis prompt
- Lets you copy the prompt to paste into Claude, ChatGPT, or Gemini

**Total ongoing cost: $0.00**

---

## Prerequisites (All Free)

You will need accounts on two free platforms:
1. **GitHub** — to store your code (github.com)
2. **Streamlit Community Cloud** — to host the app (share.streamlit.io)

---

## Step 1 — Set Up Your Files

You should have these two files from MAIC:

```
app.py
requirements.txt
```

Make sure both files are saved on your computer.

---

## Step 2 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in (or create a free account).
2. Click the **green "New"** button (top left, next to your profile).
3. Fill in:
   - **Repository name:** `maic-maritime-classifier` (or any name you like)
   - **Visibility:** ✅ Public (required for free Streamlit hosting)
   - **Add a README file:** ✅ Check this box
4. Click **"Create repository"**

---

## Step 3 — Upload Your Files to GitHub

**Option A — Browser Upload (Easiest, No Tech Required):**

1. On your new repository page, click **"Add file" → "Upload files"**
2. Drag both `app.py` and `requirements.txt` into the upload area
3. Scroll down and click **"Commit changes"**

**Option B — GitHub Desktop (Recommended if you'll update the app):**

1. Download [GitHub Desktop](https://desktop.github.com) (free)
2. Sign in and clone your new repository to your computer
3. Copy `app.py` and `requirements.txt` into the folder
4. In GitHub Desktop: write a commit message (e.g., "Initial MAIC upload") → click **"Commit to main"** → click **"Push origin"**

---

## Step 4 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your **GitHub account** (click "Continue with GitHub")
3. Click **"New app"** (top right)
4. Fill in the deployment form:

   | Field | Value |
   |-------|-------|
   | **Repository** | `your-github-username/maic-maritime-classifier` |
   | **Branch** | `main` |
   | **Main file path** | `app.py` |
   | **App URL** (optional) | `maic-maritime-classifier` (becomes your custom URL) |

5. Click **"Deploy!"**

⏱️ The app will build in about 2–3 minutes. You'll see a log of the installation process.

---

## Step 5 — Share Your App

Once deployed, you'll get a permanent public URL like:

```
https://maic-maritime-classifier.streamlit.app
```

Share this link with:
- Your UFT instructors
- Your dissertation committee
- Sailing communities and adaptive sailing organizations
- Students taking your USCG Captain's License course

**The app is live 24/7 with no server management required.**

---

## Updating the App Later

To update the app (e.g., add new prompt lenses, fix a bug):

1. Edit `app.py` on your computer
2. Upload the new version to GitHub (same "Upload files" process)
3. Streamlit automatically detects the change and re-deploys within ~60 seconds

---

## Troubleshooting Common Issues

| Problem | Solution |
|---------|----------|
| "No transcript found" error | The video doesn't have captions. Try another video or one where captions are enabled in YouTube settings. |
| App won't load / spins forever | Refresh the page. If it persists, check the Streamlit Cloud logs (click "Manage app" bottom-right corner). |
| Video shows as "Unavailable" | Make sure the YouTube video is set to **Public** (not Private or Unlisted). |
| Prompt is very short | The video may have minimal speech. Try a longer sailing vlog (30+ minutes recommended). |
| GitHub says "file too large" | `app.py` is tiny — this shouldn't happen. If your transcript somehow is saved as a file, don't upload transcripts; the app fetches them automatically. |

---

## Optional: Add a Custom Domain (Still Free)

Streamlit Community Cloud supports custom subdomains. You can change:
```
your-app.streamlit.app
```
To something more memorable by editing the app settings on share.streamlit.io.

---

## For Your UFT Presentation

When presenting to your UFT instructors, you can demonstrate:

1. **Zero-cost extraction** — paste a live YouTube sailing URL and show it pulling the transcript in real time
2. **The engineered prompt** — scroll through the generated prompt and explain each lens
3. **The analysis output** — paste the prompt into Claude.ai and show the qualitative analysis being generated
4. **The research pipeline** — explain how this tool connects YouTube → Transcript → Prompt → AI Analysis → Dissertation data

**Talking Points:**
- "This replaces what would typically require a $200/month research assistant"
- "The prompt encodes 30 years of Occupational Science theory into reusable research infrastructure"
- "Every adaptive sailing video on YouTube becomes a potential data source"
- "This is a scalable, reproducible, open-source qualitative coding pipeline"

---

## File Structure Reference

Your GitHub repository should look like this:

```
maic-maritime-classifier/
├── app.py              ← The main Streamlit application
├── requirements.txt    ← Python package dependencies
└── README.md           ← Auto-created by GitHub (optional: add description)
```

That's it. No database, no server configuration, no API keys required.

---

## Quick Reference: Zero-Cost Tool Stack

| Component | Tool | Cost |
|-----------|------|------|
| Transcript extraction | youtube-transcript-api | Free |
| Web app framework | Streamlit | Free |
| App hosting | Streamlit Community Cloud | Free |
| Code storage | GitHub | Free |
| AI analysis | Claude.ai / ChatGPT free tier | Free |
| **Total** | | **$0/month** |

---

*MAIC v1.0 — Built for UFT AI Development Course*  
*Maritime Agency & Identity Classifier — Occupational Science PhD Research Tool*
