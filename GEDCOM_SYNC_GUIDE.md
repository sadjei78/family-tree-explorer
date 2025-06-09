# 🔄 GEDCOM Sync Guide - MacFamilyTree Integration

This guide explains how to keep your web application synchronized with MacFamilyTree and maintain data consistency.

## 🎯 Overview

The family tree web application uses a GEDCOM file as its data source. To keep it updated with new information from MacFamilyTree, you need to establish a regular sync workflow.

## 📊 Current Setup

- **Primary Database**: MacFamilyTree application
- **Web Data Source**: `Weku-2025.ged` (GEDCOM 5.5.1 format)
- **Web App Version**: `{{ app_version }}`
- **Database Version**: `{{ database_version }}`

## 🔄 Sync Workflow

### Method 1: MacFamilyTree → Web App (Recommended)

#### Step 1: Export from MacFamilyTree
1. Open MacFamilyTree
2. Go to **File** → **Export** → **GEDCOM**
3. Choose these settings:
   - Format: GEDCOM 5.5.1
   - Character encoding: UTF-8
   - Include: All individuals and families
   - Include notes: Yes
   - Include media: No (for web compatibility)

#### Step 2: Update Web Application
1. **Backup current file**:
   ```bash
   cp Weku-2025.ged Weku-2025.ged.backup.$(date +%Y%m%d)
   ```

2. **Replace with new export**:
   ```bash
   cp /path/to/new/export.ged Weku-2025.ged
   ```
   
   **Alternative**: Use a different filename by setting environment variable:
   ```bash
   export GEDCOM_FILE="MyFamily-2025.ged"
   cp /path/to/new/export.ged MyFamily-2025.ged
   ```

3. **Update version numbers** in `app.py`:
   ```python
   APP_VERSION = "2025.06.2"     # Increment the last number
   DATABASE_VERSION = "1.1"      # Increment based on changes
   LAST_UPDATED = "June 2025"    # Update month/year
   ```

4. **Test the application**:
   ```bash
   python app.py
   ```

### Method 2: Web Submissions → MacFamilyTree

#### Step 1: Export Web Submissions
Visit: `http://localhost:5001/export_submissions`

#### Step 2: Create Import File
1. Copy the GEDCOM data from the export
2. Save as `submissions_import.ged`
3. Review the data for quality

#### Step 3: Import to MacFamilyTree
1. Open MacFamilyTree
2. Go to **File** → **Import** → **GEDCOM**
3. Select the `submissions_import.ged` file
4. Choose merge settings:
   - **Match by**: Name and birth date
   - **Duplicate handling**: Review manually
   - **New individuals**: Add to database

#### Step 4: Review and Merge
1. Review suggested matches
2. Resolve any conflicts
3. Accept or reject new individuals
4. Save the updated database

## 🛠️ Automation Scripts

### Backup Script (`backup_gedcom.sh`)
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"

mkdir -p $BACKUP_DIR
cp Weku-2025.ged "$BACKUP_DIR/Weku-2025_$DATE.ged"
echo "Backup created: $BACKUP_DIR/Weku-2025_$DATE.ged"
```

### Version Update Script (`update_version.py`)
```python
#!/usr/bin/env python3
import re
import sys
from datetime import datetime

def update_version(increment_type='patch'):
    # Read current app.py
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Update APP_VERSION
    current_date = datetime.now()
    year_month = f"{current_date.year}.{current_date.month:02d}"
    
    if increment_type == 'major':
        patch = "1"
    else:
        # Extract current patch number and increment
        version_match = re.search(r'APP_VERSION = "(\d+\.\d+)\.(\d+)"', content)
        if version_match:
            current_patch = int(version_match.group(2))
            patch = str(current_patch + 1)
        else:
            patch = "1"
    
    new_version = f"{year_month}.{patch}"
    
    # Update content
    content = re.sub(
        r'APP_VERSION = "[^"]+"',
        f'APP_VERSION = "{new_version}"',
        content
    )
    
    month_year = current_date.strftime("%B %Y")
    content = re.sub(
        r'LAST_UPDATED = "[^"]+"',
        f'LAST_UPDATED = "{month_year}"',
        content
    )
    
    # Write back
    with open('app.py', 'w') as f:
        f.write(content)
    
    print(f"Updated version to {new_version}")

if __name__ == "__main__":
    increment_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    update_version(increment_type)
```

## 📅 Sync Schedule Recommendations

### Option 1: Regular Intervals
- **Weekly**: For active family research periods
- **Monthly**: For normal maintenance
- **Quarterly**: For stable periods

### Option 2: Event-Based
- **After family events**: Births, deaths, marriages
- **After research sessions**: New discoveries
- **After submission reviews**: When corrections are approved

## 🔍 Data Validation

### Pre-Sync Checklist
- [ ] Backup current GEDCOM file
- [ ] Verify exported data quality
- [ ] Check for duplicate entries
- [ ] Validate date formats
- [ ] Confirm place name consistency

### Post-Sync Verification
- [ ] Test web application startup
- [ ] Verify individual count matches
- [ ] Check family relationship integrity
- [ ] Test search functionality
- [ ] Validate generation calculations

## ⚠️ Common Issues and Solutions

### Issue 1: Character Encoding Problems
**Symptoms**: Special characters display incorrectly
**Solution**: Ensure GEDCOM export uses UTF-8 encoding

### Issue 2: Large File Performance
**Symptoms**: Web app loads slowly
**Solution**: 
- Optimize GEDCOM by removing unnecessary data
- Consider splitting into multiple files if very large
- Increase server memory allocation

### Issue 3: Parsing Errors
**Symptoms**: Application fails to start
**Solution**:
- Check GEDCOM format compliance
- Validate with GEDCOM validation tools
- Review error logs for specific issues

### Issue 4: Missing Relationships
**Symptoms**: Family connections not showing
**Solution**:
- Verify FAMS/FAMC tags in GEDCOM
- Check family record integrity
- Ensure proper ID references

## 🏗️ Advanced Sync Features

### Incremental Updates (Future Enhancement)
Track changes since last sync:
```python
# Proposed enhancement
def get_changes_since(last_sync_date):
    # Compare current data with last known state
    # Return only changed/new records
    pass
```

### Conflict Resolution (Future Enhancement)
Automatic detection of data conflicts:
```python
# Proposed enhancement
def detect_conflicts(web_data, macft_data):
    # Compare same individual records
    # Flag potential conflicts for review
    pass
```

### Change Tracking (Future Enhancement)
Log all modifications:
```python
# Proposed enhancement
def log_change(change_type, record_id, old_value, new_value):
    # Track all data modifications
    # Enable rollback capabilities
    pass
```

## 📚 Best Practices

### Data Management
1. **Always backup** before making changes
2. **Test changes** in a development environment first
3. **Document** all data sources and changes
4. **Maintain** consistent naming conventions
5. **Validate** data integrity after each sync

### Version Control
1. **Use semantic versioning** for database updates
2. **Tag releases** with meaningful descriptions
3. **Keep changelogs** of major modifications
4. **Archive** old versions for reference

### Quality Assurance
1. **Regular audits** of data accuracy
2. **Peer review** of significant changes
3. **Source verification** for new information
4. **User feedback** integration

## 🎯 Troubleshooting Commands

```bash
# Check GEDCOM file validity
head -20 Weku-2025.ged
tail -20 Weku-2025.ged

# Count individuals and families
grep -c "^0 .* INDI$" Weku-2025.ged
grep -c "^0 .* FAM$" Weku-2025.ged

# Test app startup
python -c "from gedcom_parser import GedcomParser; p = GedcomParser(); data = p.parse_file('Weku-2025.ged'); print(f'Loaded {len(data[\"individuals\"])} individuals')"

# Check for encoding issues
file -bi Weku-2025.ged
```

This sync workflow ensures your web application stays current with your MacFamilyTree database while maintaining data integrity and version control. 