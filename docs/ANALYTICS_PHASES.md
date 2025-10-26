# Analytics Implementation Phases

## ✅ Phase 1: Admin Analytics Dashboard (COMPLETED)

### Overview
System-wide analytics dashboard accessible only to admin users. Provides comprehensive insights into overall system usage, model performance, and user activity.

### Features Implemented
1. **System-Wide KPIs**
   - Total registered users
   - Total predictions made
   - Average confidence score across all predictions
   - Average processing time per prediction

2. **Time Series Analysis**
   - Daily prediction trends (last 30 days)
   - Peak usage times by hour of day
   - Class distribution over time

3. **Model Performance Monitoring**
   - Prediction class distribution (pie chart)
   - Average confidence by class (bar chart)
   - Low-confidence predictions alert table (< 70%)

4. **User Activity Analytics**
   - Most active users (last 7 days)
   - User engagement metrics
   - Login and activity tracking

5. **Database Enhancements**
   - Added `user_activity` table for tracking logins, predictions, PDF downloads
   - Extended `predictions` table with `confidence_score` and `processing_time_ms`

### Access Control
- Only users listed in `settings.admin_users` can access the Admin Dashboard
- Default admin username: `"admin"`
- Configure in `src/config/settings.py` or via `.env` file

### Technologies Used
- **Plotly Express**: Interactive charts and visualizations
- **Pandas**: Data manipulation and aggregation
- **SQLite**: Analytics data storage
- **Streamlit Tabs**: Multi-page layout

---

## ✅ Phase 1.5: User Analytics (IMPLEMENTED)

### Overview
Personal analytics dashboard showing individual user's prediction history, patterns, and usage statistics.

### Features Implemented
1. **Personal KPIs**
   - Total predictions made by user
   - Average confidence score for user's predictions
   - Total logins

2. **Activity Breakdown**
   - Bar chart showing user's activities (logins, predictions, PDF downloads)
   - Account creation date
   - Last activity timestamp

3. **Personal Trends**
   - Daily prediction count (last 30 days)
   - Confidence score trend over time
   - Threshold indicator (70% line)

4. **User-Specific Distribution**
   - Pie chart of user's predictions by class
   - Recent predictions table with details

### Access Control
- All authenticated users can access "My Analytics"
- Shows only data specific to the logged-in user
- No access to other users' data

---

## 🚀 Phase 2: Advanced User Analytics & Reports (PLANNED)

### Goals
Enhance user analytics with downloadable reports, comparisons, and actionable insights.

### Proposed Features

#### 2.1 Downloadable User Reports
**Priority: High**
- **PDF Summary Report**
  - Personal statistics summary
  - Charts embedded in PDF
  - Month-over-month comparison
  - Generated via fpdf2 (already in dependencies)
  
- **CSV Data Export**
  - Export all user predictions to CSV
  - Include metadata (timestamps, confidence, classes)
  - Enable external analysis (Excel, etc.)

#### 2.2 Comparative Analytics
**Priority: Medium**
- **Benchmarking Against System Average**
  - "Your confidence vs. system average"
  - "Your prediction volume vs. average user"
  - Percentile ranking (e.g., "Top 10% most active users")

- **Time-Based Comparisons**
  - Week-over-week change in activity
  - Month-over-month trend indicators
  - "Your predictions are up 25% this week!"

#### 2.3 Prediction Insights & Recommendations
**Priority: Medium**
- **Usage Patterns**
  - Most common prediction time (hour of day)
  - Most frequent class predicted
  - Average confidence by day of week

- **Quality Metrics**
  - Percentage of high-confidence predictions (>80%)
  - Percentage requiring review (<70%)
  - Suggestion: "Consider reviewing 3 low-confidence cases"

#### 2.4 Goal Setting & Gamification
**Priority: Low**
- **Achievement Badges**
  - "First 10 Predictions"
  - "100 Predictions Milestone"
  - "Consistent User" (7 days in a row)
  
- **Progress Tracking**
  - Set personal goals (e.g., "100 predictions this month")
  - Progress bar visualization
  - Streak tracking

#### 2.5 Enhanced Visualizations
**Priority: Medium**
- **Heatmaps**
  - Prediction activity heatmap (day × hour)
  - Confidence score heatmap by class and time

- **Interactive Filters**
  - Filter predictions by date range
  - Filter by class type
  - Filter by confidence threshold

- **Comparative Line Charts**
  - Overlay user trend with system average
  - Multiple class trends on same chart

#### 2.6 Email Reports (Advanced)
**Priority: Low**
- **Weekly Summary Email**
  - Automated weekly digest
  - Key metrics + charts
  - Requires email service integration (SMTP)

- **Alert Notifications**
  - Email when confidence drops below threshold
  - Notify on prediction milestones

---

## 📋 Implementation Roadmap

### Phase 2.1: Downloadable Reports (Week 1)
**Tasks:**
1. Create PDF report generator for user analytics
   - Reuse existing `pdf_report.py` structure
   - Add chart embedding (convert Plotly to images)
   - Include summary statistics

2. Add CSV export functionality
   - Query user predictions with all metadata
   - Convert to CSV format
   - Add download button in "My Analytics" tab

3. Add "Export" section in user analytics
   - "Download My Report (PDF)" button
   - "Export My Data (CSV)" button

**Database Changes:** None required

**New Files:**
- `src/utils/reporting/user_report_pdf.py`
- `src/utils/analytics_export.py`

---

### Phase 2.2: Comparative Analytics (Week 2)
**Tasks:**
1. Add comparison metrics to analytics.py
   - `get_user_vs_system_comparison(username)`
   - `get_user_percentile(username)`
   - `get_user_week_over_week(username)`

2. Add comparison visualizations
   - Dual-axis charts (user vs. system)
   - Delta indicators (↑ 25% from last week)
   - Percentile badges

3. Create "Insights" section in My Analytics
   - Display comparative metrics
   - Show trend indicators
   - Highlight achievements

**Database Changes:**
- Add `user_stats_cache` table (optional, for performance)

**New Functions:**
- `analytics.get_system_average_confidence()`
- `analytics.get_user_rank_by_activity(username)`
- `analytics.get_user_time_comparison(username, periods=4)`

---

### Phase 2.3: Prediction Insights (Week 3)
**Tasks:**
1. Implement usage pattern analysis
   - Peak prediction hour for user
   - Most common class
   - Day-of-week patterns

2. Add quality metrics
   - High/medium/low confidence breakdown
   - Review recommendations
   - Quality score (composite metric)

3. Create "Insights" card in UI
   - "💡 Insights for You" section
   - Bullet points with recommendations
   - Visual indicators (✅ ⚠️ 📈)

**Database Changes:** None required

**New Functions:**
- `analytics.get_user_peak_hour(username)`
- `analytics.get_user_quality_metrics(username)`
- `analytics.get_user_recommendations(username)`

---

### Phase 2.4: Gamification (Week 4)
**Tasks:**
1. Design achievement/badge system
   - Define badge criteria
   - Create badge icons/emojis
   - Track achievement progress

2. Implement badge checking
   - Check on login
   - Check after each prediction
   - Store achievements in DB

3. Display achievements
   - "🏆 Achievements" section in My Analytics
   - Badge gallery (earned + locked)
   - Progress bars for in-progress badges

**Database Changes:**
- Add `user_achievements` table
  - `id`, `username`, `badge_id`, `earned_at`, `progress`

**New Files:**
- `src/utils/gamification.py`
- `src/config/badges.json` (badge definitions)

---

### Phase 2.5: Enhanced Visualizations (Week 5)
**Tasks:**
1. Add heatmap visualizations
   - Install `plotly.graph_objects` (already available)
   - Create heatmap for hour × day activity
   - Create confidence score heatmap

2. Add interactive filters
   - Date range picker (Streamlit date_input)
   - Class filter (multiselect)
   - Confidence slider

3. Implement filtered queries
   - Modify analytics functions to accept filters
   - Apply filters to all visualizations
   - Update charts dynamically

**Database Changes:** None required

**Dependencies:** None (Plotly already installed)

---

### Phase 2.6: Email Reports (Week 6) - OPTIONAL
**Tasks:**
1. Set up email service
   - Configure SMTP settings
   - Add email credentials to .env
   - Test email delivery

2. Create email template
   - HTML email with embedded charts
   - Plain text fallback
   - Unsubscribe link

3. Implement scheduling
   - Weekly cron job or background task
   - Check user preferences (opt-in)
   - Send digest emails

**Database Changes:**
- Add `user_preferences` table
  - `username`, `email_notifications`, `email_address`

**New Dependencies:**
- `smtplib` (built-in)
- `email` (built-in)
- Optional: `schedule` or `APScheduler` for automation

**New Files:**
- `src/utils/email_service.py`
- `src/utils/reporting/email_template.html`

---

## 🎯 Quick Wins for Next Session

### 1. PDF Report Export (30 minutes)
Add a simple "Download My Report" button that generates a PDF with:
- User's total predictions
- Class distribution chart (as image)
- Recent predictions table

### 2. CSV Export (15 minutes)
Add "Export to CSV" button that downloads all user predictions with columns:
- ID, Filename, Predicted Class, Confidence, Date, Patient ID

### 3. Comparison Metrics (20 minutes)
Add a simple comparison card:
- "Your avg confidence: X% vs. System avg: Y%"
- "You are in the top Z% of users by activity"

### 4. Insights Section (30 minutes)
Add a "💡 Insights" section showing:
- Your most common prediction time
- Your most predicted class
- Number of predictions needing review

---

## 🛠️ Technical Considerations

### Performance
- **Caching:** Use `@st.cache_data` for analytics queries
- **Pagination:** For large datasets, add pagination to tables
- **Indexing:** Add DB indexes on `user`, `created_at`, `predicted_label`

### Security
- **Data Isolation:** Ensure users only see their own data
- **Admin Check:** Verify admin status on every admin dashboard load
- **SQL Injection:** Use parameterized queries (already implemented)

### Scalability
- **Background Jobs:** Move heavy analytics to background tasks
- **Pre-aggregation:** Cache daily/weekly summaries in separate table
- **Chart Optimization:** Limit data points in time series (e.g., last 90 days max)

### User Experience
- **Loading States:** Show spinners for slow queries
- **Empty States:** Friendly messages when no data exists
- **Tooltips:** Add explanations for metrics (ℹ️ icon)
- **Responsive Design:** Ensure charts work on mobile (Streamlit handles this)

---

## 📊 Success Metrics

### Phase 1 Success Criteria ✅
- [x] Admin dashboard accessible only to admin users
- [x] At least 8 different visualizations
- [x] Real-time data updates
- [x] No performance issues with 1000+ predictions

### Phase 2 Success Criteria
- [ ] Users can download PDF reports with charts
- [ ] Users can export their data to CSV
- [ ] Comparative metrics show user vs. system average
- [ ] At least 3 actionable insights per user
- [ ] Badge system with 5+ achievement types
- [ ] User satisfaction: 4.5+ / 5 stars

---

## 🎨 UI/UX Mockup Ideas

### User Analytics Layout
```
┌─────────────────────────────────────────────────┐
│  📊 My Analytics                                │
│  Personal analytics for username                │
├─────────────────────────────────────────────────┤
│  My Activity Summary                            │
│  [Total Predictions] [Avg Confidence] [Logins]  │
├─────────────────────────────────────────────────┤
│  💡 Insights for You                            │
│  • Your confidence is 5% above average ✅       │
│  • You're in the top 20% of active users 🏆    │
│  • 2 predictions need review ⚠️                 │
├─────────────────────────────────────────────────┤
│  📈 My Predictions Over Time                    │
│  [Interactive Line Chart]                       │
├─────────────────────────────────────────────────┤
│  🎯 My Class Distribution                       │
│  [Pie Chart]          [Confidence by Class]     │
├─────────────────────────────────────────────────┤
│  🏆 My Achievements                             │
│  [Badge: First 10 ✅] [Badge: 100 Predictions ❌]│
├─────────────────────────────────────────────────┤
│  🔍 My Recent Predictions                       │
│  [Filterable Table with Date Range Picker]     │
├─────────────────────────────────────────────────┤
│  📥 Export My Data                              │
│  [Download PDF Report] [Export to CSV]          │
└─────────────────────────────────────────────────┘
```

---

## 📝 Notes

- Phase 1 (Admin Dashboard) is fully implemented and tested
- Phase 1.5 (User Analytics) is implemented with basic features
- Phase 2 features are modular and can be implemented independently
- Each Phase 2 sub-feature is self-contained (can cherry-pick)
- Consider user feedback before implementing gamification features
- Email reports should be opt-in only (privacy/spam concerns)

---

**Last Updated:** October 24, 2025  
**Status:** Phase 1 ✅ Complete | Phase 1.5 ✅ Complete | Phase 2 📋 Planned
