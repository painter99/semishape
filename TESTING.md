# SemiShape Refactored Testing Guide

## ⚠️ Complete Uninstall Instructions (Old Plugin)

Before testing the refactored version, completely remove all traces of the old SemiShape plugin.

### Step 1: Disable the Plugin in Agent Zero UI

1. Open Agent Zero UI
2. Go to **Settings → Plugins**
3. Find **SemiShape** in the list
4. Click **Disable** (or **Remove** if available)
5. Confirm the action

### Step 2: Remove Plugin Symlink

```bash
# Remove the extension symlink
rm -f /a0/extensions/python/agent_init/_10_semishape.py

# Verify it's removed
ls -la /a0/extensions/python/agent_init/ | grep semishape
# (should show nothing)
```

### Step 3: Remove Skill Copy

```bash
# Remove the skill copy
rm -rf /a0/usr/skills/semishape

# Verify it's removed
ls -la /a0/usr/skills/ | grep semishape
# (should show nothing)
```

### Step 4: Clean Cache Directories

```bash
# Remove plugin cache (if exists)
rm -rf /a0/usr/projects/semishape/data/cache
rm -rf /a0/usr/projects/semishape/data/logs

# Remove generated output files (but keep examples)
rm -f /a0/usr/projects/semishape/output/*.stl
rm -f /a0/usr/projects/semishape/output/*.step

# Verify .gitkeep remains
ls -la /a0/usr/projects/semishape/output/
# (should show only .gitkeep)
```

### Step 5: Verify Complete Removal

```bash
# Check no semishape references remain
grep -r "semishape" /a0/extensions/ 2>/dev/null || echo "✓ No semishape in extensions"
grep -r "semishape" /a0/usr/skills/ 2>/dev/null || echo "✓ No semishape in skills"

# Check plugin directory is clean
ls -la /a0/usr/projects/semishape/ | head -20
```

### Step 6: Restart Agent Zero

```bash
# Restart the Agent Zero service
sudo systemctl restart agent-zero
# or manually restart the application
```

---

## 🚀 Install Refactored Version (Testing)

### Option A: Direct Git Clone (Development)

```bash
# Clone the refactored branch
git clone -b refactor/english-cleanup-v1 https://github.com/painter99/semishape.git /tmp/semishape-test

# Navigate to the plugin directory
cd /tmp/semishape-test

# Verify structure
ls -la
# Should show: plugin.yaml, hooks.py, tools/, src/, etc.
```

### Option B: Download as ZIP (Manual Installation)

1. Go to GitHub: https://github.com/painter99/semishape
2. Click **Code** → **Branches** → select `refactor/english-cleanup-v1`
3. Click **Code** → **Download ZIP**
4. Extract to `/tmp/semishape-test/`

```bash
# After extracting
cd /tmp/semishape-test/semishape-refactor/  # (or whatever folder name GitHub created)

# Verify structure
ls -la
# Should show: plugin.yaml, hooks.py, tools/, src/, etc.
```

### Step 1: Install Plugin Dependencies

```bash
# Navigate to plugin directory
cd /tmp/semishape-test  # (or your extracted path)

# Run the dependency installer
python3 initialize.py

# Verify installations
python3 -c "import build123d; print('✓ build123d installed')"
python3 -c "import chromadb; print('✓ chromadb installed')"
python3 -c "import duckduckgo_search; print('✓ duckduckgo_search installed')"
```

### Step 2: Register Plugin in Agent Zero

1. Open Agent Zero UI
2. Go to **Settings → Plugins**
3. Click **Install Plugin**
4. Select **Custom** or **Local Path**
5. Paste or browse to: `/tmp/semishape-test`
6. Click **Install**
7. Agent Zero should run `hooks.py install()` automatically

### Step 3: Enable the Plugin

1. In **Settings → Plugins**, find **SemiShape**
2. Click **Enable**
3. Agent Zero may restart

### Step 4: Verify Plugin Loaded

```bash
# Check symlink was created
ls -la /a0/extensions/python/agent_init/ | grep semishape
# Should show: _10_semishape.py → /tmp/semishape-test/extensions/...

# Check skill was copied
ls -la /a0/usr/skills/semishape/
# Should show: SKILL.md and other files

# Check in Agent Zero console
# You should see: "[SemiShape] ✓ Plugin ready — CAD generation available."
```

---

## ✅ Test Each Tool

### Test 1: Code Generation (`@semishape_generate`)

**In Agent Zero chat:**

```
@semishape_generate description="Create a simple 50×30×10 mm box" language="en"
```

**Expected result:**
- ✅ CAD code block is generated
- ✅ Code uses `with BuildPart() as part:`
- ✅ STL file is exported to `/tmp/semishape-test/output/model_*.stl`
- ✅ File size > 1 KB

**If it fails:**
- Check: `[SemiShape] ✓ Plugin ready` message in console
- Verify API key is set: `echo $API_KEY_OPENROUTER` or `echo $OPENROUTER_API_KEY`
- Check error message in chat response

### Test 2: Code Execution (`@semishape_execute`)

**In Agent Zero chat:**

```
@semishape_execute code="from build123d import *\nwith BuildPart() as p:\n    Box(100, 50, 20)" export_format="stl" output_name="test_box"
```

**Expected result:**
- ✅ Code executes without error
- ✅ STL file exported to `/tmp/semishape-test/output/test_box.stl`
- ✅ File size > 1 KB
- ✅ Message shows: `📦 STL: /path/to/test_box.stl`

**If it fails:**
- Check: build123d imported correctly
- Verify code has `with BuildPart() as p:` syntax
- Check sandbox execution timeout (should be ~60 sec)

### Test 3: Documentation Search (`@semishape_rag_search`)

**In Agent Zero chat:**

```
@semishape_rag_search query="how to use fillet" use_web=true
```

**Expected result:**
- ✅ Returns 3-5 documentation snippets
- ✅ Shows source file paths (e.g., `data/docs/direct_api_reference.rst`)
- ✅ Optionally shows web results from DuckDuckGo
- ✅ No errors in console

**If it fails:**
- Check: `data/docs/` directory exists and contains .rst files
- Verify duckduckgo-search is installed
- Try without web: `use_web=false`

---

## 🧪 Integration Test

**Complete workflow in Agent Zero:**

```
# 1. Search docs first
@semishape_rag_search query="extrude mode"

# 2. Generate code from description
@semishape_generate description="Create a 100×50×10 mm plate with a 20 mm cylindrical hole in the center" language="en"

# 3. If code looks good, re-export to STEP format
@semishape_execute code="<paste code from above>" export_format="step" output_name="plate_with_hole"
```

**Verification:**
- ✅ All 3 tools respond without error
- ✅ Generated files in `/tmp/semishape-test/output/`
- ✅ Both STL and STEP formats available
- ✅ Files have reasonable sizes (> 1 KB)

---

## 📋 Troubleshooting

### Plugin Not Appearing in Settings

```bash
# Check plugin.yaml exists and is valid
cat /tmp/semishape-test/plugin.yaml

# Verify hooks.py exists
ls -la /tmp/semishape-test/hooks.py

# Check for errors in Agent Zero console
```

### "API key not found" Error

```bash
# Set API key
export API_KEY_OPENROUTER="sk-your-key-here"

# Or add to Agent Zero secrets in UI:
# Settings → Secrets → Add → API_KEY_OPENROUTER → your-key
```

### "build123d not installed" Error

```bash
# Install manually
python3 -m pip install build123d>=0.10.0

# Or re-run initialize.py
python3 initialize.py
```

### No Documentation Files Found

```bash
# Verify data/docs exists
ls /tmp/semishape-test/data/docs/ | head
# Should show: *.rst, *.py files (600+ total)

# If empty, clone from GitHub didn't include submodules
# The docs/ folder is a Git submodule — see README.md for setup
```

### STL Export Fails

```bash
# Check if BuildPart object is detected
# Add debug output to your test code:
print("part =", part)

# Verify export directory is writable
touch /tmp/semishape-test/output/test_write.txt
rm /tmp/semishape-test/output/test_write.txt
```

---

## 📊 Success Checklist

Before declaring the refactored version ready:

- [ ] Old plugin completely removed (no symlinks, no skills copies)
- [ ] New plugin installs without errors
- [ ] `@semishape_generate` creates CAD code + exports STL
- [ ] `@semishape_execute` runs code and exports to multiple formats
- [ ] `@semishape_rag_search` finds build123d docs
- [ ] All tools output professional messages with file paths
- [ ] No hardcoded models — uses Agent Zero active model
- [ ] Error messages are clear and actionable
- [ ] Generated STL/STEP files are valid (can open in Fusion 360, Cura, etc.)

---

## 🎯 Next Steps After Testing

1. **Merge PR** on GitHub (`refactor/english-cleanup-v1` → `main`)
2. **Tag Release** as `v1.0.0` on main branch
3. **Publish to Plugin Repository** (if available)
4. **Create Release Notes** with migration guide for users of old version

---

## 📞 Support

If tests fail, enable debug logging:

```bash
# Check Agent Zero logs
tail -f /var/log/agent-zero/agent.log

# Or run with verbose output
PYTHONUNBUFFERED=1 python3 initialize.py
```
