# 📌 Git Workflow: Create Branch & Push Code

## Complete Step-by-Step Guide

---

## Step 1: Create a New Branch

```bash
# Create and switch to a new branch
git checkout -b feature/terrawatch-complete

# OR if you prefer a more descriptive name
git checkout -b feature/featherless-ai-integration

# OR with the current date
git checkout -b feature/terrawatch-2026-03-15
```

**What this does:**
- Creates a new branch
- Automatically switches to it
- Your work is now isolated from `main`

**Verify:**
```bash
git branch
# You should see:
#   main
# * feature/terrawatch-complete  (the * means you're on this branch)
```

---

## Step 2: Add All Changes

```bash
# Add all modified and new files
git add .

# Verify what will be committed
git status
```

**You should see:**
```
On branch feature/terrawatch-complete

Changes to be committed:
  (new file):   COMPLETION_SUMMARY.md
  (new file):   IMPLEMENTATION.md
  (new file):   MANUAL_TESTING.md
  (new file):   QUICK_REFERENCE.md
  (new file):   START_HERE.md
  (new file):   TESTING.md
  (new file):   .env.example
  (modified):   README.md
  (modified):   backend/main.py
  (modified):   backend/ai_client.py
  (modified):   backend/config.py
  (modified):   backend/insurance_engine.py
  (modified):   backend/insurance_engine.py
  (modified):   backend/models.py
  (modified):   backend/risk_engine.py
  (modified):   requirements.txt
```

---

## Step 3: Commit Your Changes

```bash
# Commit with a descriptive message
git commit -m "feat: Complete TerraWatch implementation with Featherless AI integration

- T1: Project scaffold with FastAPI
- T2: IPCC climate scenarios for 2024-2050
- T3: Climate risk assessment endpoint
- T4: Qwen-72B narration engine
- T5: Qwen-7B insurance premium calculator
- T6: Open-Meteo city geocoding
- T7: Pre-cache demo scenarios (9 scenarios)
- BONUS: Gemma-3-27B satellite imagery analysis
- Full documentation and testing guides"
```

**Alternative (shorter):**
```bash
git commit -m "feat: Add complete TerraWatch API with all 7 tasks + Featherless AI"
```

**Verify:**
```bash
git log --oneline
# You should see your new commit at the top
```

---

## Step 4: Push to GitHub

```bash
# Push your branch to GitHub
git push origin feature/terrawatch-complete
```

**First time pushing a new branch?**
Git might suggest:
```
git push --set-upstream origin feature/terrawatch-complete
```

Just copy and paste that command, or the simpler version above also works.

**Verify:**
```bash
git branch -v
# You should see:
#   main                                 abc1234 Initial commit
# * feature/terrawatch-complete         def5678 feat: Complete TerraWatch...
```

---

## Step 5: Create a Pull Request (Optional but Recommended)

Once pushed, GitHub will show a notification to create a Pull Request.

**Via GitHub Website:**
1. Go to: https://github.com/samib6/terrawatch
2. You'll see a green button: "Compare & pull request"
3. Click it
4. Add title: `Complete TerraWatch with Featherless AI`
5. Add description:
   ```
   ## What's New
   - All 7 tasks implemented
   - Featherless AI integration (Qwen-72B, Qwen-7B, Gemma-3-27B)
   - Complete documentation
   - Full test suite
   
   ## Features
   - Climate risk assessment
   - AI-powered narration
   - Insurance premium calculation
   - City geocoding
   - Demo cache system
   - Satellite imagery analysis
   ```
6. Click "Create pull request"

---

## Step 6: Merge to Main (After Review)

If you want to merge this branch to `main`:

**Option A: Merge locally**
```bash
# Switch to main branch
git checkout main

# Update main with latest from GitHub
git pull origin main

# Merge the feature branch
git merge feature/terrawatch-complete

# Push to GitHub
git push origin main
```

**Option B: Merge via GitHub (Recommended)**
1. Go to your PR on GitHub
2. Click "Merge pull request" button
3. Choose merge method:
   - "Create a merge commit" (default, keeps history)
   - "Squash and merge" (clean history)
   - "Rebase and merge" (linear history)
4. Confirm

---

## Complete Command Sequence (Copy & Paste)

```bash
cd /Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch

# 1. Create branch
git checkout -b feature/terrawatch-complete

# 2. Add all changes
git add .

# 3. Commit
git commit -m "feat: Complete TerraWatch implementation with all 7 tasks + Featherless AI"

# 4. Push to GitHub
git push origin feature/terrawatch-complete

# 5. Check status
git status
git log --oneline
```

---

## Verify Everything Worked

```bash
# Check your branch is created and pushed
git branch -a
# You should see:
#   main
# * feature/terrawatch-complete
#   remotes/origin/feature/terrawatch-complete

# Check your commit is there
git log -1
# Should show your commit message

# Check GitHub has it
# Go to: https://github.com/samib6/terrawatch/branches
# You should see: feature/terrawatch-complete
```

---

## Common Issues & Solutions

### Issue: "fatal: 'origin' does not appear to be a remote repository"

```bash
# Check your remotes
git remote -v

# If empty, add the remote
git remote add origin https://github.com/samib6/terrawatch.git

# Then push again
git push origin feature/terrawatch-complete
```

### Issue: "Permission denied (publickey)"

You need to set up SSH or use HTTPS:

**Option 1: Use HTTPS (easier)**
```bash
git remote set-url origin https://github.com/samib6/terrawatch.git
git push origin feature/terrawatch-complete
```

**Option 2: Set up SSH** (see GitHub docs)

### Issue: "Updates were rejected because the tip of your current branch is behind"

```bash
# Pull latest from GitHub first
git pull origin main

# Then push your branch
git push origin feature/terrawatch-complete
```

### Issue: "Would you like to set the upstream tracking information?"

Just do:
```bash
git push -u origin feature/terrawatch-complete
```

---

## Best Practices

✅ **Always:**
- Create a feature branch (not pushing to main directly)
- Use descriptive branch names: `feature/`, `fix/`, `docs/`
- Write clear commit messages
- Test locally before pushing
- Use pull requests for code review

❌ **Never:**
- Force push to shared branches: `git push -f`
- Commit large files or secrets
- Work directly on `main`
- Commit without testing

---

## Branch Naming Conventions

```
feature/new-feature          → New functionality
fix/bug-fix-name             → Bug fix
docs/documentation-update    → Documentation only
refactor/cleanup             → Code cleanup
test/test-additions          → Test additions
```

**Examples for this project:**
- `feature/terrawatch-complete`
- `feature/featherless-ai-integration`
- `docs/api-documentation`
- `feat/add-vision-model`

---

## What Each File Does

When you push, GitHub will receive:

```
Modified files (7):
- README.md                  → Updated project overview
- backend/main.py            → All 9 endpoints
- backend/ai_client.py       → Featherless integration
- backend/config.py          → Configuration
- backend/insurance_engine.py → Insurance logic
- backend/models.py          → Response schemas
- backend/risk_engine.py     → Risk calculations
- requirements.txt           → Dependencies

New files (8):
- COMPLETION_SUMMARY.md      → Project status
- IMPLEMENTATION.md          → Task breakdown
- MANUAL_TESTING.md          → Testing guide
- QUICK_REFERENCE.md         → URL cheat sheet
- START_HERE.md              → Quick start
- TESTING.md                 → Detailed tests
- .env.example               → Environment template
- quickstart.sh              → Setup script

New directory (2 files):
- scripts/warmup_cache.py    → Cache generation
- scripts/test_api.py        → Test suite
```

---

## After Pushing - Next Steps

1. **Share your branch link:**
   ```
   https://github.com/samib6/terrawatch/tree/feature/terrawatch-complete
   ```

2. **Create a Pull Request:**
   ```
   https://github.com/samib6/terrawatch/pulls
   ```

3. **Share with teammates:**
   - Slack/Teams: "Check out my PR at [link]"
   - Email: Include PR link
   - Code review: Assign reviewers

4. **After approval, merge to main:**
   - Click "Merge pull request" on GitHub

---

## Quick Reference Card

```bash
# 1. Create branch
git checkout -b feature/name

# 2. Make changes (already done ✓)

# 3. Add all
git add .

# 4. Commit
git commit -m "descriptive message"

# 5. Push
git push origin feature/name

# 6. Create PR on GitHub (optional)

# 7. Merge to main (after review)
git checkout main && git pull && git merge feature/name && git push
```

---

## Final Checklist

- [ ] Branch created and named properly
- [ ] All changes staged (`git add .`)
- [ ] Commit message is descriptive
- [ ] Pushed to GitHub (`git push origin ...`)
- [ ] Branch visible on GitHub website
- [ ] Ready for pull request

---

**You're all set! Your code is now on a feature branch and ready to share! 🚀**
