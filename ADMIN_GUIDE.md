# 🛠️ Admin Dashboard Guide

This guide covers the new admin dashboard and flexible GEDCOM filename configuration.

## 🎯 Admin Dashboard Overview

The admin dashboard provides a centralized interface for managing your family tree application.

**Access**: Visit `/admin` in your browser (e.g., `http://localhost:5001/admin`)

## 📊 Dashboard Features

### System Overview
- **Live Statistics**: Individuals, families, submissions, feedback counts
- **Version Information**: App version, database version, current GEDCOM filename
- **Quick Actions**: Export GEDCOM, backup data

### API Endpoints Section
- **Listed Endpoints**: All available API endpoints with direct access links
- **Test Functionality**: Test all endpoints with one click
- **Direct Links**: Click to open any endpoint in a new tab

### Family Submissions Management
- **Real-time Display**: All user submissions with formatting and timestamps
- **Submission Types**: Corrections (red), new persons (green)
- **Details Shown**: Submitter info, changes requested, sources, notes
- **Export Options**: Download all submissions in JSON or GEDCOM format

### User Feedback Management
- **Categorized Feedback**: Questions, bugs, features, general feedback
- **Color-coded Types**: Visual identification of feedback categories
- **Contact Information**: Submitter names and emails for follow-up
- **Page Context**: Shows which page the feedback came from

## 🔗 Navigation Integration

Admin links are now available in:
- **Homepage**: Admin button in main action buttons
- **Explorer**: Admin link in header navigation
- **Admin Dashboard**: Links back to all main pages

## 🗂️ GEDCOM Filename Flexibility

### Current Behavior
By default, the app looks for `Weku-2025.ged` in the project directory.

### Using Different Filenames

#### Method 1: Environment Variable
```bash
export GEDCOM_FILE="MyFamily-2025.ged"
python3 app.py
```

#### Method 2: Command Line (temporary)
```bash
GEDCOM_FILE="MyFamily-2025.ged" python3 app.py
```

#### Method 3: Modify app.py
Change the line in `app.py`:
```python
GEDCOM_FILENAME = os.getenv('GEDCOM_FILE', 'YourFilename.ged')
```

### Examples of Different Filenames
- `AdjeiFamily-2025.ged`
- `FamilyTree-v2.ged`
- `Heritage-June2025.ged`
- `Genealogy-Latest.ged`

### Benefits
1. **Multiple Databases**: Switch between different family tree databases
2. **Version Control**: Keep multiple versions with descriptive names
3. **Backup Management**: Use dated filenames for backups
4. **Development/Production**: Use different files for testing vs live data

## 🔄 Workflow Integration

### Daily Administration Tasks
1. **Check Dashboard**: Visit `/admin` to see pending submissions
2. **Review Feedback**: Process user questions and bug reports
3. **Export Data**: Download submissions for processing
4. **Monitor System**: Check stats and endpoint health

### Weekly Maintenance
1. **Process Submissions**: Review and approve/reject submissions
2. **Update Database**: Import approved changes to MacFamilyTree
3. **Backup Files**: Create timestamped backups
4. **Respond to Users**: Answer feedback and questions

### Database Updates
1. **Export from Admin**: Use dashboard to export approved submissions
2. **Import to MacFamilyTree**: Follow GEDCOM sync guide
3. **Export Updated GEDCOM**: Get new file from MacFamilyTree
4. **Replace/Rename**: Update web app with new data
5. **Update Version**: Increment version numbers in app.py
6. **Test via Admin**: Use dashboard to verify everything works

## 📱 Mobile Compatibility

The admin dashboard is fully responsive and works on:
- **Desktop**: Full feature access
- **Tablet**: Optimized layout
- **Mobile**: Touch-friendly interface with stacked cards

## 🔐 Security Considerations

### Current Setup
The admin dashboard is currently open access. For production use, consider:

1. **Basic Authentication**: Add password protection
2. **IP Restrictions**: Limit access to specific IP addresses
3. **HTTPS**: Use SSL certificates for secure connections
4. **User Roles**: Implement different permission levels

### Example Protection (Future Enhancement)
```python
@app.route('/admin')
@require_auth  # Decorator for authentication
def admin_dashboard():
    # Admin logic here
```

## 🛠️ Troubleshooting

### Common Issues

#### Dashboard Not Loading
- Check that Flask app is running
- Verify `/admin` route is accessible
- Check browser console for JavaScript errors

#### Empty Submissions/Feedback
- Verify JSON files exist (`family_submissions.json`, `family_feedback.json`)
- Check file permissions
- Ensure submissions have been made through the forms

#### GEDCOM File Not Found
- Verify filename matches `GEDCOM_FILENAME` variable
- Check file exists in project directory
- Confirm file permissions allow reading

#### Endpoint Test Failures
- Check that all required endpoints are defined
- Verify Flask app is running properly
- Check for any import/dependency errors

### Useful Commands

```bash
# Check current GEDCOM filename
python3 -c "from app import GEDCOM_FILENAME; print(f'Using: {GEDCOM_FILENAME}')"

# Verify file exists
ls -la *.ged

# Check submissions
cat family_submissions.json | python3 -m json.tool

# Check feedback
cat family_feedback.json | python3 -m json.tool
```

## 🎯 Future Enhancements

Potential improvements for the admin dashboard:

1. **Approval Workflow**: Mark submissions as approved/rejected
2. **Email Integration**: Send responses directly from dashboard
3. **Data Validation**: Check submission data quality
4. **Analytics**: Track usage patterns and popular features
5. **Bulk Operations**: Process multiple submissions at once
6. **Backup Automation**: Scheduled backups with restore capability
7. **User Management**: Multiple admin users with different permissions

The admin dashboard provides a powerful interface for managing your family tree application efficiently while maintaining data quality and user engagement. 