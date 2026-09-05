# 🚀 GIT PUSHer — Push Your Code to GitHub Without Knowing Git

> You wrote code. You want it on GitHub. Run one command. Done.

---

## 🤔 What Even Is This?

This tool takes your project folder and **automatically puts it on GitHub** for you.

It handles everything:
- Never used Git before? It sets it up.
- No GitHub repo yet? It creates one.
- Something goes wrong mid-push? It fixes it and tries again.

You don't need to know what `git commit` or `git push` means. You just run this.

---

## 📋 Before You Start (Do This Once)

You need **3 things** installed on your computer. Here's how to get each one:

---

### Thing 1 — Python

Python is the language this tool is written in.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** On the first screen, check the box that says **"Add Python to PATH"** before clicking Install

To check it worked, open Command Prompt and type:
```
py --version
```
You should see something like `Python 3.x.x`

---

### Thing 2 — Tesseract OCR

This lets the tool "read" your screen to detect errors.

1. Go to **https://github.com/UB-Mannheim/tesseract/wiki**
2. Download the Windows installer (the `.exe` file)
3. Run it and click through — keep all the default settings
4. It installs to `C:\Program Files\Tesseract-OCR\` — don't change this

---

### Thing 3 — A GitHub Account

If you don't have one:
1. Go to **https://github.com**
2. Click **Sign up** and create a free account

---

## 🔑 Getting Your GitHub Token

A token is like a password specifically for this tool. Here's how to get one:

1. Log into GitHub
2. Click your **profile picture** (top right) → **Settings**
3. Scroll all the way down the left sidebar → click **Developer settings**
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Give it a name like `git-pusher`
7. Set **Expiration** to `No expiration` (or however long you want)
8. Check the **`repo`** checkbox (that's all you need)
9. Scroll down → click **Generate token**
10. **COPY THE TOKEN NOW** — you won't be able to see it again!

It'll look something like: `abcdefghijklmnopqrstuvwxyz1234556`

---

## ⚡ Setting Up GIT PUSHer

Open **Command Prompt** (`Win + R` → type `cmd` → press Enter) and run:

```
cd "c:\Users\*****\OneDrive\Documents\GIT PUSHer"
push.bat
```

The first time it runs, it will ask you **2 questions**:

```
GitHub Username
> yourGitHubUsername

GitHub Personal Access Token
> (paste your token here — the text won't show, that's normal)
```

That's it. Your answers are saved locally. **It will never ask again.**

---

## 🎯 Using It (Every Time You Want to Push Code)

Open Command Prompt and run:

```
push.bat
```

Then answer the 2 questions it asks:

```
Enter project path (or . for current dir): C:\Users\You\Desktop\MyProject
Commit message (leave blank for auto):     added login page
```

And watch it do everything automatically. ✅

---

## 🧪 Other Ways to Run It

**Push the current folder you're in:**
```
push.bat .
```

**Push a specific folder:**
```
push.bat "C:\Users\You\Desktop\MyProject"
```

**Push with a custom message:**
```
push.bat "C:\MyProject" -m "fixed the bug"
```

**Make the repo private:**
```
push.bat "C:\MyProject" --private
```

---

## 🔄 Switching GitHub Accounts

If you want to use a different GitHub account:
```
push.bat --reset
```
Then run `push.bat` again — it'll ask for your new credentials.

---

## 🆘 Something Went Wrong?

| Problem | Fix |
|---|---|
| `Python not found` | Reinstall Python and make sure to check "Add to PATH" |
| `Token is wrong / access denied` | Run `push.bat --reset` and paste your token again |
| `Tesseract not found` | Install Tesseract from the link above, keep default path |
| `Push failed after 4 tries` | Check your internet connection, try again |
| `Merge conflict` | The tool auto-resolves it — your code always wins |

---

## 🔒 Is My Token Safe?

Yes. Your token is saved in a file called `.env` on **your computer only**. It never gets uploaded or shared anywhere. The `.gitignore` file makes sure it's always excluded from any uploads.

-------------

## 📁 What Are All These Files?

You don't need to touch any of these, but just so you know:

| File | What it does |
|---|---|
| `push.bat` | The launcher you double-click or run |
| `gitpusher.py` | The brain of the tool |
| `git_engine.py` | Handles all the Git stuff (init, commit, push, conflicts) |
| `vision_engine.py` | Watches the screen for errors using OCR |
| `setup_credentials.py` | Manages your saved login info |
| `.env` | Where your username and token are saved (don't share this file) |
