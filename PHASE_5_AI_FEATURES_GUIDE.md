# Phase 5: AI Features and Profile Management Guide

## Overview

Phase 5 adds two powerful administrative features:
1. **AI-Powered Quiz Generation** - Create quizzes from documents using AI
2. **Dynamic Profile Viewer** - Comprehensive student profile management

## Feature 1: AI-Powered Quiz Generation

### Purpose
Generate multiple-choice quizzes automatically from PDF, DOCX, TXT, or Markdown documents using AI providers (OpenAI, Google Gemini, or Anthropic Claude).

### Access
- **URL:** `http://localhost:5000/quiz-ai/create`
- **Required Role:** Admin or Teacher
- **Navigation:** Admin Dashboard → "AI-Powered Features" → "Create Quiz with AI"

### How to Use

#### Step 1: Upload Document
1. Click the file upload area or drag & drop a document
2. Supported formats:
   - PDF (.pdf)
   - Word Documents (.docx)
   - Text Files (.txt)
   - Markdown (.md)
3. Maximum file size: 5MB

#### Step 2: Configure Quiz Parameters
- **Quiz Title:** Name of the quiz (e.g., "Biology Chapter 5: Photosynthesis")
- **Number of Questions:** Slider from 1-50 (recommended: 10-30)
- **Difficulty Level:** Easy, Medium, or Hard
- **AI Provider:** Choose from:
  - OpenAI GPT-3.5 (recommended for accuracy)
  - Google Gemini (good for comprehensive answers)
  - Anthropic Claude (balanced approach)

#### Step 3: Generate Quiz
1. Click "Generate Quiz with AI"
2. Wait for processing (typically 30-60 seconds)
3. Review the generated questions in the preview

#### Step 4: Save Quiz
- Click "Save Quiz" to store in database
- Quiz becomes available for students immediately
- Linked to your account as creator

### API Key Configuration (Optional for Testing)

To use AI providers, set environment variables in your `.env` file:

```env
# OpenAI (for GPT-3.5)
OPENAI_API_KEY=sk-... (from https://platform.openai.com/api-keys)

# Google Gemini
GOOGLE_API_KEY=... (from https://aistudio.google.com/app/apikey)

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-... (from https://console.anthropic.com/)
```

### Testing Without API Keys

- Use sample documents from `app/static/uploads/sample_documents/`
- System will simulate AI responses if keys not configured
- In production, at least one API key recommended

### View AI-Generated Quizzes
- **URL:** `http://localhost:5000/quiz-ai/list`
- Shows all AI-generated quizzes with:
  - Creator (Admin/Teacher name)
  - AI Provider used
  - Source document
  - Number of questions
  - Creation date

### Technical Details

#### Supported File Types and Processing
- **PDF:** Extracted using PyPDF2
- **DOCX:** Extracted using python-docx
- **TXT:** Direct text reading
- **Markdown:** Parsed and cleaned

#### AI Integration
- Uses prompt engineering to generate structured questions
- Returns JSON with title, description, and questions array
- Each question has: question text, 4 options, correct answer, explanation

#### Data Storage
- Quiz saved to `quizzes` table with:
  - `ai_generated` = True
  - `ai_provider` = selected provider
  - `source_document` = original filename
  - `created_by` = current user ID

---

## Feature 2: Dynamic Student Profile Viewer

### Purpose
View, filter, search, and export comprehensive student profiles with activity tracking and quiz attempt history.

### Access
- **URL:** `http://localhost:5000/admin/profiles/`
- **Required Role:** Admin only
- **Navigation:** Admin Dashboard → "Student Profiles" → "View All Profiles"

### How to Use

#### Main Profile List View

**Statistics Cards (Top):**
- Total Students: Overall count
- Complete Profiles: Students with all info filled
- Completion Rate: Percentage of complete profiles
- Incomplete Profiles: Need profile updates

**Filter and Search:**

1. **Search Box:**
   - Search by student name, ID, or email
   - Real-time filtering as you type

2. **Class Filter:**
   - Dropdown to select specific class (e.g., "10-A", "12-B")
   - Leave blank to show all classes

3. **School Filter:**
   - Select school name
   - Helps in multi-school deployments

4. **Gender Filter:**
   - Options: All, Male, Female, Other
   - Filters by student gender

5. **Sort Options:**
   - Sort by: Created Date, Name, Class, School
   - Order: Ascending/Descending

6. **Apply Filters:**
   - Click "Apply Filters" to execute search

#### Profile List Table

**Columns:**
- Student ID (unique identifier)
- Name (full name)
- Email (contact email)
- Class (class/level)
- School (school name)
- Gender (M/F/Other)
- Created (account creation date)
- Actions (view details/profile)

**Pagination:**
- 20 profiles per page
- Previous/Next navigation
- Page indicator (e.g., "Page 1 of 5")

**CSV Export:**
- Click "Export to CSV" button
- Downloads all filtered results as CSV file
- Useful for reports and data analysis

#### Detailed Profile View

**Access:**
- Click "View" button next to any student in the list
- **URL:** `http://localhost:5000/admin/profiles/<student_id>`

**Profile Sections:**

**1. Personal Information**
- Full Name
- Gender
- Date of Birth
- Nationality
- Religion

**2. Contact Information**
- Email Address
- Primary Phone
- Secondary Phone
- Residential Address
- District/Region
- Post Office

**3. Academic Information**
- School Name
- Class/Level
- Section
- Roll Number

**4. Account Status**
- Account Status (Active/Inactive)
- Account Created Date
- Last Login Date/Time
- Last IP Address Used

**5. Quick Actions**
- Reset Password: Send password reset link
- Toggle Activation: Activate/Deactivate account
- Send Email: Send direct email to student

**6. Recent Activities**
- Table of last 20 activities
- Columns:
  - Timestamp (date & time)
  - Activity Type (Login, Upload Note, Attempt Quiz, etc.)
  - Action (brief description)
  - Details (additional information)
- Useful for monitoring student engagement

**7. Quiz Attempts**
- Table of last 10 quiz attempts
- Columns:
  - Quiz Name
  - Score (points/total)
  - Percentage (success rate)
  - Time Taken (duration)
  - Attempt Date
  - Status (Pass/Fail)
- Shows student's assessment performance

### Use Cases

#### Use Case 1: Monitor Student Engagement
1. Open Profile Viewer
2. Sort by "Last Login"
3. Identify inactive students
4. Click their name to see activity history
5. Take action (send message, parent contact, etc.)

#### Use Case 2: Class-wise Analysis
1. Filter by Class: "10-A"
2. Apply filters
3. Click "Export to CSV"
4. Analyze class performance in spreadsheet
5. Identify struggling students

#### Use Case 3: School Performance Review
1. Filter by School: "Delhi Public School"
2. Check Completion Rate
3. Identify incomplete profiles
4. Contact students to update information

#### Use Case 4: Student Investigation
1. Search by student ID: "EA24C01"
2. Click "View" to open detailed profile
3. Review activity history (when logged in, what activities)
4. Check quiz attempts and scores
5. Assess overall performance

#### Use Case 5: Bulk Reporting
1. Set desired filters (class, school, gender)
2. Click "Export to CSV"
3. Use in reports, parent communication, or analysis

### Profile Statistics API

**Endpoint:** `GET /admin/profiles/api/stats`

Returns JSON with distribution:
```json
{
  "by_class": {"10-A": 25, "10-B": 22, ...},
  "by_school": {"DPS": 50, "Mayo": 45, ...},
  "by_gender": {"Male": 60, "Female": 35, "Other": 2},
  "total_students": 97,
  "complete_profiles": 85,
  "completion_percentage": 87.6,
  "inactive_students": 8,
  "no_login_students": 5
}
```

### Technical Details

#### Database Queries
- Profile list queries optimized with proper indexes
- Filtering/sorting done at database level for performance
- Pagination prevents loading large result sets

#### CSV Export
- Includes all profile fields
- Headers: ID, Name, Email, Class, School, Gender, Created Date, Last Login
- Can be opened in Excel, Google Sheets, etc.

#### Data Privacy
- Only Admin can access profiles
- No sensitive data exposed in lists
- Detailed views for authorized users only

---

## Configuration & Troubleshooting

### Common Issues

#### Issue: "Invalid AI Provider"
**Solution:** Ensure selected provider is one of: openai, gemini, claude

#### Issue: "File too large"
**Solution:** Maximum file size is 5MB. Compress document or split into smaller parts.

#### Issue: "Unsupported file type"
**Solution:** Use PDF, DOCX, TXT, or Markdown files only. Convert other formats first.

#### Issue: "No profiles found"
**Solution:** 
- Check filters (may be too restrictive)
- Ensure students exist in database
- Clear all filters and try again

#### Issue: "API call failed"
**Solution:**
- Check internet connection
- Verify API keys in .env file
- Try different AI provider
- Check API provider's status page

### Performance Optimization

**For Large Datasets:**
- Use CSV export instead of viewing all profiles
- Apply specific filters before searching
- Use pagination (navigate through pages)

**For AI Quiz Generation:**
- Start with smaller documents (5-10 pages)
- Use 10-20 questions for faster processing
- Consider time limits (30-60 seconds typical)

### Database Maintenance

**Reset AI Quiz Data:**
```bash
# Delete all AI-generated quizzes
DELETE FROM quiz WHERE ai_generated = 1;
```

**Reset Profile Statistics:**
```bash
# Refresh last login timestamps
# (automatic on next login)
```

---

## API Endpoints Summary

| Feature | Endpoint | Method | Role | Purpose |
|---------|----------|--------|------|---------|
| Create AI Quiz | `/quiz-ai/create` | GET/POST | Admin/Teacher | Create quiz from document |
| AI Quiz Preview | `/quiz-ai/preview` | POST | Admin/Teacher | Preview generated quiz |
| List AI Quizzes | `/quiz-ai/list` | GET | Admin/Teacher | View all AI-generated quizzes |
| View All Profiles | `/admin/profiles/` | GET | Admin | List all student profiles |
| Profile Details | `/admin/profiles/<id>` | GET | Admin | View specific student profile |
| Profile Stats | `/admin/profiles/api/stats` | GET | Admin | Get profile statistics |
| Export Profiles | `/admin/profiles/export` | GET | Admin | Download profiles as CSV |

---

## Best Practices

### For Quiz Creation
1. ✅ Use clear, well-formatted documents
2. ✅ Include key concepts and definitions
3. ✅ Review AI-generated questions before saving
4. ✅ Edit questions if needed after generation
5. ❌ Don't rely solely on AI (always review)

### For Profile Management
1. ✅ Regularly check incomplete profiles
2. ✅ Monitor inactive students
3. ✅ Use filters for targeted analysis
4. ✅ Export data for reports/analysis
5. ❌ Don't share CSV exports unencrypted

### For Admin Dashboard
1. ✅ Check dashboard daily for updates
2. ✅ Monitor pending notes/approvals
3. ✅ Review activity logs for security
4. ✅ Use new features to improve engagement
5. ❌ Don't ignore low engagement warnings

---

## Data Security & Privacy

### What Data is Stored?
- Document text extracted (not original file)
- Generated quiz questions (AI output)
- Student activity logs (timestamp + action)
- Profile information (only visible to admin)

### Privacy Safeguards
- Only Admin role can access profiles
- Activity logs not shown to students
- CSV exports should be handled securely
- Uploaded documents deleted after extraction

### Compliance
- Follows GDPR guidelines for student data
- Activity logging for audit trails
- User consent for data processing
- Ability to export/delete user data

---

## Future Enhancements

### Planned Features (Phase 6)
- [ ] Real-time activity dashboard
- [ ] Bulk email to student groups
- [ ] Advanced analytics and charts
- [ ] Mobile app for quiz taking
- [ ] Auto-detection of struggling students
- [ ] Integration with more AI providers
- [ ] Quiz difficulty auto-detection
- [ ] Plagiarism detection for notes
- [ ] Student progress tracking dashboard
- [ ] Parent portal access

---

## Support & Resources

**Need Help?**
- Check `README.md` for general setup
- See `TESTING_GUIDE.md` for test scenarios
- Review `DOCUMENTATION.md` for architecture

**External Resources:**
- OpenAI API Docs: https://platform.openai.com/docs
- Google Gemini API: https://ai.google.dev/
- Anthropic Claude API: https://docs.anthropic.com/

**Contact:**
- For issues, create a GitHub issue
- For features, submit via feature request
- For deployment help, see hosting guides

---

## Version History

**Phase 5.0 (Current)**
- Initial release of AI Quiz Generator
- Profile Viewer with filtering/export
- Admin Dashboard integration
- Support for 3 AI providers
- CSV export functionality

---

**Last Updated:** January 2024
**Status:** Production Ready ✅
