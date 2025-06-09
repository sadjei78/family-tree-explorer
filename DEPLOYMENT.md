# 🚀 Deployment Guide - Family Tree Explorer

This guide will help you deploy the Family Tree Explorer app so others can access it online.

## 🎯 Quick Deploy Options

### Option 1: Render (Recommended - Free & Easy)

**Render** offers free hosting perfect for this Flask app.

#### Steps:

1. **Prepare your code:**
   - Ensure all files are committed to your repository
   - The app is already configured for production deployment

2. **Sign up for Render:**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub (recommended)

3. **Create a Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `family-tree-explorer` (or your choice)
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python app.py`

4. **Set Environment Variables:**
   ```
   FLASK_ENV=production
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - You'll get a URL like: `https://family-tree-explorer.onrender.com`

#### ✅ Render Advantages:
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ SSL certificates included
- ✅ Easy to configure

---

### Option 2: Railway (Alternative Free Option)

**Railway** is another excellent free hosting platform.

#### Steps:

1. **Sign up for Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub:**
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python and deploys

3. **Set Environment Variables:**
   ```
   FLASK_ENV=production
   ```

4. **Access your app:**
   - Railway provides a URL automatically

---

### Option 3: PythonAnywhere (Beginner-Friendly)

**PythonAnywhere** is great for Python beginners.

#### Steps:

1. **Sign up:**
   - Go to [pythonanywhere.com](https://pythonanywhere.com)
   - Create a free account

2. **Upload files:**
   - Use the file manager to upload your project files
   - Or clone from GitHub using the console

3. **Create Web App:**
   - Go to Web tab → "Add a new web app"
   - Choose Flask
   - Point to your `app.py` file

4. **Configure:**
   - Set up the WSGI file to point to your app
   - Install requirements via console

---

### Option 4: Heroku (Paid but Reliable)

**Note**: Heroku discontinued free tiers but offers paid hosting.

#### Steps:

1. **Install Heroku CLI:**
   ```bash
   # On macOS
   brew install heroku/brew/heroku
   
   # On Windows/Linux
   # Download from heroku.com
   ```

2. **Login and create app:**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set FLASK_ENV=production
   ```

---

## 📝 Pre-Deployment Checklist

Before deploying, ensure you have:

- ✅ `requirements.txt` - Lists all Python dependencies
- ✅ `Procfile` - Tells the server how to run your app
- ✅ `runtime.txt` - Specifies Python version
- ✅ Production-ready `app.py` - Uses environment variables
- ✅ All files committed to Git/GitHub

## 🔧 Configuration Files

### `requirements.txt`
```
Flask==2.3.3
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
```

### `Procfile`
```
web: python app.py
```

### `runtime.txt`
```
python-3.11.0
```

## 🌐 After Deployment

Once deployed, your app will be available at a public URL. Users can:

1. **Browse the family tree** - Search and explore family members
2. **View relationships** - See how people are connected
3. **Check generation labels** - Understand family timeline
4. **Submit contributions** - Add corrections and new family members
5. **Export data** - Download submissions in GEDCOM format

## 📊 Monitoring & Updates

### Checking App Health
- Most platforms provide logs and monitoring
- Check for any errors in the deployment logs
- Test all features after deployment

### Updating the App
1. Make changes to your code locally
2. Commit and push to GitHub
3. Most platforms auto-deploy on push
4. Or trigger manual deployments

### Managing User Contributions
- Submissions are saved to `family_submissions.json`
- Export them regularly using the app's export feature
- Review and import into your genealogy software

## 🚨 Troubleshooting

### Common Issues:

**Port Binding Error:**
- Solution: Use environment variables (already configured)

**Missing Dependencies:**
- Solution: Check `requirements.txt` is complete

**File Not Found:**
- Solution: Ensure `Weku-2025.ged` is included in deployment

**Slow Loading:**
- Solution: Free tiers may have cold starts, upgrade for better performance

### Getting Help:
- Check platform-specific documentation
- Use platform support channels
- Create GitHub issues for app-specific problems

## 💡 Tips for Success

1. **Start with Render** - Easiest for beginners
2. **Test locally first** - Make sure everything works before deploying
3. **Use environment variables** - Already configured for production
4. **Monitor submissions** - Check user contributions regularly
5. **Backup data** - Export family submissions periodically

## 🎉 Share Your Deployment

Once deployed, share the URL with:
- Family members for testing and contributions
- Genealogy communities for feedback
- Social media to gather more family connections

---

**🚀 Ready to deploy? Choose your platform and follow the steps above!**

## 🚀 Production Deployment

### Prerequisites
- Python 3.8+
- Git
- Web server (nginx/Apache) or cloud platform (Heroku, DigitalOcean, AWS, etc.)

### Step 1: Environment Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Weku-2025
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with production values:**
   ```bash
   # REQUIRED: Set secure values
   ADMIN_PASSWORD=your_super_secure_admin_password_here
   SECRET_KEY=your_random_secret_key_for_sessions_here
   
   # Application settings
   PORT=5000
   FLASK_ENV=production
   GEDCOM_FILE=your-family-file.ged
   ```

### Step 3: Security Checklist

- [ ] **Strong admin password** (12+ characters, mixed case, numbers, symbols)
- [ ] **Random secret key** (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] **HTTPS enabled** (SSL certificate configured)
- [ ] **Firewall configured** (only necessary ports open)
- [ ] **Regular backups** scheduled
- [ ] **Environment variables secure** (`.env` not in version control)

### Step 4: Platform-Specific Deployment

#### Option A: Heroku
```bash
# Set environment variables
heroku config:set ADMIN_PASSWORD="your_secure_password"
heroku config:set SECRET_KEY="your_secret_key"
heroku config:set FLASK_ENV="production"

# Deploy
git push heroku main
```

#### Option B: DigitalOcean App Platform
1. Connect your GitHub repository
2. Set environment variables in the dashboard:
   - `ADMIN_PASSWORD`
   - `SECRET_KEY`
   - `FLASK_ENV=production`

#### Option C: Traditional Server
```bash
# Install gunicorn for production
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or use systemd service (recommended)
sudo systemctl enable family-tree
sudo systemctl start family-tree
```

### Step 5: Post-Deployment

1. **Test the deployment:**
   - Visit your domain
   - Try admin login with new password
   - Test all major features

2. **Monitor logs:**
   ```bash
   tail -f /var/log/family-tree/app.log
   ```

3. **Set up backups:**
   - Schedule regular GEDCOM file backups
   - Export submissions/feedback regularly

## 🔧 Development vs Production

| Feature | Development (.env) | Production |
|---------|-------------------|------------|
| Password | `FamilyTree2025_SecureAdmin!` | Your secure password |
| Secret Key | Development key | Random 32+ chars |
| Debug Mode | `FLASK_ENV=development` | `FLASK_ENV=production` |
| Port | `5001` | `5000` or cloud-assigned |
| HTTPS | Optional | Required |

## 🛡️ Security Notes

1. **Never commit `.env` files** - they're in `.gitignore`
2. **Use environment variables** in production platforms
3. **Enable HTTPS** for all production deployments
4. **Regular security updates** for all dependencies
5. **Monitor access logs** for suspicious activity

## 🆘 Troubleshooting

### Common Issues:

1. **"Address already in use"**
   - Change PORT in `.env` file
   - Kill existing processes: `pkill -f python.*app.py`

2. **"Invalid password"**
   - Check ADMIN_PASSWORD in `.env`
   - Ensure no extra spaces/characters

3. **"Module not found"**
   - Verify virtual environment is activated
   - Run: `pip install -r requirements.txt`

4. **"Permission denied"**
   - Check file permissions
   - Ensure web server can read files

### Contact
For deployment issues, contact the development team or create an issue in the repository. 