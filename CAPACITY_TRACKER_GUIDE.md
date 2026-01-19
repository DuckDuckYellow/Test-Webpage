# Recruitment Capacity Tracker - Implementation Guide

## 📋 Overview

The Recruitment Capacity Tracker is now live at: `/projects/capacity-tracker`

This tool calculates team capacity based on vacancy complexity with the following rules:
- **Easy vacancies**: Maximum 30 at full capacity (each = 3.33% capacity)
- **Medium vacancies**: Maximum 20 at full capacity (each = 5% capacity)
- **Hard vacancies**: Maximum 12 at full capacity (each = 8.33% capacity)

Mixed workloads combine cumulatively.

---

## 🎯 Features Implemented

### ✅ Core Functionality
- Manual input form for multiple recruiters
- Dynamic "Add Recruiter" functionality (JavaScript)
- Real-time capacity calculations
- Color-coded status indicators
- Remaining capacity calculations
- Team summary statistics
- Form validation and error handling

### ✅ UI/UX
- Matches site design (Bootstrap 5 + custom styles)
- Mobile responsive
- Clear visual hierarchy
- Color-coded status badges:
  - 🟢 Green (0-69%): Available
  - 🟡 Amber (70-89%): Near Capacity
  - 🔴 Red (90-100%): At Capacity
  - ⚫ Dark Red (>100%): Overloaded
- Professional, clean interface

### ✅ Integration
- Added to Projects page with "active" status
- Breadcrumb navigation
- Consistent with site navigation

---

## 📁 Files Modified/Created

### Modified Files:
1. **app.py**
   - Added `request` import
   - Updated PROJECTS list (line 30)
   - Added calculation functions (lines 108-215)
   - Added `/projects/capacity-tracker` route (lines 258-323)

2. **templates/projects.html**
   - Added active projects section
   - Separated active vs planned projects
   - Added hover effects

### New Files:
1. **templates/projects/capacity_tracker.html**
   - Complete capacity tracker interface
   - Dynamic form with JavaScript
   - Results table and team summary
   - Embedded styles for capacity indicators

---

## 🧪 Testing Checklist

### Test Cases to Verify:

#### 1. **Basic Form Functionality**
- [ ] Load page at `/projects/capacity-tracker`
- [ ] Page displays correctly with hero section
- [ ] Form shows initial recruiter input row
- [ ] "Add Another Recruiter" button works
- [ ] "Remove" button appears and works for additional recruiters
- [ ] Form validation: empty name shows error
- [ ] "Reset Form" button works with confirmation

#### 2. **Calculation Scenarios**

**Scenario A: Underutilized (Available Status)**
- Input: Easy=10, Medium=0, Hard=0
- Expected: 33.3% capacity, Green "Available" badge
- Expected message: "Can take 20 more easy OR 13 more medium OR 8 more hard vacancies"

**Scenario B: Near Capacity (Amber Status)**
- Input: Easy=20, Medium=5, Hard=0
- Expected: 91.7% capacity, Amber "Near Capacity" badge
- Expected message: Shows small remaining capacity

**Scenario C: At Capacity (Red Status)**
- Input: Easy=27, Medium=0, Hard=0
- Expected: 90% capacity, Red "At Capacity" badge
- Expected message: "Can take 3 more easy OR 2 more medium OR 1 more hard vacancies"

**Scenario D: Overloaded (Dark Red Status)**
- Input: Easy=30, Medium=10, Hard=8
- Expected: 216.7% capacity, Dark Red "Overloaded" badge
- Expected message: "Overloaded by 35 easy OR 23 more medium OR 14 more hard vacancies"

**Scenario E: All Medium**
- Input: Easy=0, Medium=15, Hard=0
- Expected: 75% capacity, Amber "Near Capacity" badge

**Scenario F: All Hard**
- Input: Easy=0, Medium=0, Hard=9
- Expected: 75% capacity, Amber "Near Capacity" badge

**Scenario G: Mixed Load**
- Input: Easy=10, Medium=5, Hard=3
- Expected: 83.3% capacity, Amber "Near Capacity" badge

**Scenario H: Zero Vacancies**
- Input: Easy=0, Medium=0, Hard=0
- Expected: 0% capacity, Green "Available" badge
- Expected message: "Can take 30 more easy OR 20 more medium OR 12 more hard vacancies"

#### 3. **Multi-Recruiter Testing**
- [ ] Add 3-4 recruiters with different workloads
- [ ] All recruiters display in results table
- [ ] Each row has correct calculations
- [ ] Status badges show correct colors

#### 4. **Team Summary Testing**
- [ ] Team summary card appears after calculation
- [ ] Total recruiter count is correct
- [ ] Average capacity is correct
- [ ] Status breakdown counts are correct
- [ ] Team health indicator shows appropriate status:
  - "Good - Capacity Available" when avg < 50%
  - "Healthy - Balanced Load" when avg 50-70%
  - "Warning - High Utilization" when >50% at/over capacity
  - "Critical - Team Overloaded" when >30% overloaded

#### 5. **Error Handling**
- [ ] Negative numbers show error message
- [ ] Non-numeric input shows error message
- [ ] Multiple errors display correctly
- [ ] Errors clear on successful submission

#### 6. **Mobile Responsiveness**
- [ ] Test on mobile view (DevTools responsive mode)
- [ ] Table is scrollable on small screens
- [ ] Form inputs stack properly
- [ ] Buttons are full-width on mobile
- [ ] Text is readable at all sizes

#### 7. **Navigation**
- [ ] "Back to Projects" link works
- [ ] Breadcrumb links work
- [ ] Main nav highlights "Projects" correctly
- [ ] From Projects page, capacity tracker card is clickable

---

## 🔢 Calculation Logic Explained

### Individual Capacity Formula:
```python
capacity_used = (easy / 30) + (medium / 20) + (hard / 12)
capacity_percentage = capacity_used × 100
```

### Status Determination:
- `capacity_used > 1.0` → Overloaded (dark red)
- `capacity_used >= 0.9` → At Capacity (red)
- `capacity_used >= 0.7` → Near Capacity (amber)
- `capacity_used < 0.7` → Available (green)

### Remaining Capacity:
```python
remaining = 1.0 - capacity_used

If remaining >= 0:
    additional_easy = remaining × 30
    additional_medium = remaining × 20
    additional_hard = remaining × 12
else:
    overload_easy = |remaining| × 30
    overload_medium = |remaining| × 20
    overload_hard = |remaining| × 12
```

### Team Summary:
- **Average Capacity**: Sum of all capacity percentages / team size
- **Team Health**:
  - Critical: >30% overloaded
  - Warning: >50% at/over capacity
  - Underutilized: avg < 50%
  - Healthy: balanced load

---

## 🎨 Design Notes

### Color Scheme (matches site):
- Primary Dark: `#2c3e50`
- Primary Accent: `#667eea`
- Secondary Accent: `#764ba2`

### Status Colors:
- Available: `#28a745` (green)
- Near Capacity: `#ffc107` (amber)
- At Capacity: `#dc3545` (red)
- Overloaded: `#8b0000` (dark red)

### Team Health Colors:
- Healthy: `#d4edda` background, `#28a745` border
- Underutilized: `#d1ecf1` background, `#17a2b8` border
- Warning: `#fff3cd` background, `#ffc107` border
- Critical: `#f8d7da` background, `#dc3545` border

---

## 🚀 Deployment Steps

### On PythonAnywhere:

1. **Pull changes from Git**
   ```bash
   cd ~/Test-Webpage
   git pull origin claude/add-recruitment-tracker-LIulS
   ```

2. **Reload web app**
   - Go to Web tab in PythonAnywhere
   - Click "Reload the442.pythonanywhere.com"

3. **Test the feature**
   - Visit: https://the442.pythonanywhere.com/projects/capacity-tracker
   - Run through testing checklist

---

## 📝 Usage Instructions (for end users)

### To Calculate Team Capacity:

1. Navigate to Projects → Recruitment Capacity Tracker
2. Enter first recruiter's details:
   - Name (required)
   - Number of easy, medium, and hard vacancies (default 0)
3. Click "+ Add Another Recruiter" to add more team members
4. Click "Calculate Capacity" to see results
5. Review individual and team capacity metrics
6. Use "Reset Form" to start over

### Reading the Results:

**Individual Results Table:**
- Each row shows a recruiter's workload and capacity
- Capacity percentage shows how much of full capacity is used
- Status badge indicates workload level (color-coded)
- Remaining capacity shows additional work that can be taken

**Team Summary:**
- Total team size
- Average capacity utilization
- Breakdown by status category
- Overall team health indicator

---

## 🔮 Future Enhancements (Not in this version)

- Session 2: Excel upload functionality
- Session 3: Save calculations / data persistence
- Session 4: Historical tracking and trends
- Session 5: Charts and visualization
- Session 6: Team comparison features

---

## 🐛 Known Limitations

1. **No data persistence**: Calculations are not saved (by design for Session 1)
2. **No export functionality**: Results cannot be exported yet
3. **Session-based only**: Each form submission is independent
4. **No historical data**: Cannot track changes over time

These are intentional limitations for Session 1 and will be addressed in future sessions.

---

## 💡 Key Learning Points

### Flask Concepts Used:
- GET/POST route handling
- Form data processing (`request.form`)
- Dynamic form field naming (`name_0`, `name_1`, etc.)
- Template rendering with data
- Error handling and validation

### Frontend Concepts:
- JavaScript DOM manipulation
- Dynamic form field creation
- Event listeners
- Form validation
- Bootstrap 5 components
- CSS custom properties
- Responsive design

### Python Concepts:
- Dictionary unpacking (`**dict`)
- List comprehensions
- F-strings for formatting
- Function documentation
- Business logic separation

---

## ✅ Implementation Checklist

- [x] Calculation functions in app.py
- [x] Flask route with GET/POST handling
- [x] HTML template with form
- [x] JavaScript for dynamic form
- [x] Results display with color coding
- [x] Team summary section
- [x] Error handling and validation
- [x] Mobile responsive design
- [x] Integration with Projects page
- [x] Documentation created

---

## 📞 Support

If you encounter any issues:
1. Check browser console for JavaScript errors (F12)
2. Verify Flask logs on PythonAnywhere
3. Ensure all files were uploaded correctly
4. Clear browser cache if styles don't appear
5. Test in incognito mode to rule out caching issues

---

**Version**: 1.0
**Date**: January 2026
**Status**: ✅ Ready for deployment
