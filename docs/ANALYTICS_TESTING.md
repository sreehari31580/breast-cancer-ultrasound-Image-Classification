# Testing the Analytics Dashboard

## Quick Test Guide

### Step 1: Create Admin User
The default admin username is **"admin"**. You need to register this user first.

1. Open the app: http://localhost:8501
2. Go to the "Register" tab
3. Create user with username: `admin` and any password
4. This user will have admin privileges

### Step 2: Test Admin Dashboard
1. Log in as `admin`
2. You should see **3 tabs**: 🔬 Prediction | 📊 My Analytics | 🔐 Admin Dashboard
3. Click on "🔐 Admin Dashboard" tab
4. You should see:
   - System-wide KPIs (Total Users, Total Predictions, etc.)
   - Predictions Over Time chart
   - Class Distribution pie chart
   - Confidence by Class bar chart
   - Low Confidence Predictions table
   - Most Active Users chart
   - Peak Usage Times chart

### Step 3: Test User Analytics
1. While logged in as `admin` (or any user)
2. Click on "📊 My Analytics" tab
3. You should see:
   - Personal KPIs (My Total Predictions, My Avg Confidence, Total Logins)
   - My Activity Breakdown
   - My Predictions Over Time
   - My Prediction Class Distribution
   - My Recent Predictions table
   - My Confidence Score Trend

### Step 4: Create Regular User
1. Log out (refresh the page)
2. Register a new user (e.g., username: `testuser`)
3. Log in as `testuser`
4. You should see **2 tabs**: 🔬 Prediction | 📊 My Analytics
5. **No Admin Dashboard tab** (as expected for non-admin users)

### Step 5: Generate Test Data
To see charts with data:

1. **Make predictions**: Upload several images and get predictions
2. **Check analytics**: After 3-5 predictions, refresh the analytics tabs
3. Charts will populate with your data

### Step 6: Test Activity Tracking
The app now tracks:
- **Logins**: Logged when you authenticate
- **Predictions**: Logged when you upload an image
- **PDF Downloads**: Logged when you download a report

Check the "My Activity Breakdown" chart in My Analytics to see these tracked.

---

## Adding More Admin Users

### Option 1: Via Environment Variable
1. Create a `.env` file in the project root (copy from `.env.example`)
2. Add line:
   ```env
   ADMIN_USERS=admin,doctor1,sreehari
   ```
3. Restart the Streamlit app
4. Users `admin`, `doctor1`, and `sreehari` will have admin access

### Option 2: Via settings.py
1. Open `src/config/settings.py`
2. Find the line:
   ```python
   admin_users: list[str] = Field(default=["admin"])
   ```
3. Add usernames:
   ```python
   admin_users: list[str] = Field(default=["admin", "doctor1", "sreehari"])
   ```
4. Restart the Streamlit app

---

## Troubleshooting

### Issue: No data in analytics charts
**Solution:** Make some predictions first. Analytics need data to visualize.

### Issue: "admin" user doesn't see Admin Dashboard
**Checks:**
1. Verify you're logged in as exactly `admin` (case-sensitive)
2. Check console for any errors
3. Verify `settings.admin_users` contains `"admin"`
4. Restart the Streamlit app

### Issue: Charts not loading
**Checks:**
1. Ensure Plotly is installed: `pip install plotly>=5.14`
2. Check browser console (F12) for JavaScript errors
3. Try refreshing the page (Ctrl+F5)

### Issue: Database errors after update
**Solution:** Run database migration:
```powershell
python -c "from src.utils.db_utils import init_db; init_db()"
```

---

## Expected Behavior

### For Admin Users:
- ✅ See "🔐 Admin Dashboard" tab
- ✅ See system-wide metrics (all users)
- ✅ See "My Analytics" tab (personal metrics)
- ✅ Can access all prediction features

### For Regular Users:
- ❌ No "🔐 Admin Dashboard" tab
- ✅ See "My Analytics" tab (personal metrics only)
- ✅ Can access all prediction features
- ✅ Can only see their own data (data isolation)

---

## Sample Test Workflow

### Complete Test Scenario:
1. **Register admin:** username=`admin`, password=`admin123`
2. **Register user1:** username=`alice`, password=`alice123`
3. **Register user2:** username=`bob`, password=`bob123`

4. **Login as alice:**
   - Upload 3 images, make predictions
   - Download 1 PDF report
   - Check "My Analytics" (should show 3 predictions, 1 PDF download)

5. **Login as bob:**
   - Upload 2 images, make predictions
   - Check "My Analytics" (should show 2 predictions, NO alice's data)

6. **Login as admin:**
   - Check "Admin Dashboard":
     - Total Users: 3 (admin, alice, bob)
     - Total Predictions: 5 (3 from alice + 2 from bob)
     - Most Active Users: alice (3), bob (2)
   - Check "My Analytics":
     - Should show 0 predictions (admin hasn't made any)

---

## Performance Notes

### With Small Data (<100 predictions):
- All charts load instantly
- No performance issues

### With Medium Data (100-1000 predictions):
- Charts may take 1-2 seconds to load
- Consider adding loading spinners (Phase 2)

### With Large Data (>1000 predictions):
- Consider implementing:
  - Pagination for tables
  - Date range filters
  - Data aggregation/caching
  - Database indexes

---

## Next Steps (Phase 2)

After testing Phase 1, you can implement:
1. **PDF Report Export** (User Analytics summary as PDF)
2. **CSV Data Export** (Download all user predictions)
3. **Comparative Metrics** (User vs. System average)
4. **Insights & Recommendations** (Smart suggestions)
5. **Gamification** (Badges, achievements, streaks)

See `docs/ANALYTICS_PHASES.md` for detailed Phase 2 plan.

---

**Last Updated:** October 24, 2025  
**App Version:** v1.0  
**Analytics Version:** Phase 1 Complete
