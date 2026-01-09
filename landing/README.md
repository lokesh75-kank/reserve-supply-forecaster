# Landing Page

This directory contains the static landing page for the Reserve Supply Forecaster project.

## Files

- `index.html` - Main HTML file
- `styles.css` - Stylesheet with modern, responsive design
- `script.js` - JavaScript for interactivity and animations

## Deployment

The landing page is automatically deployed to GitHub Pages using GitHub Actions when changes are pushed to the `main` branch.

### Setup Instructions

1. **Enable GitHub Pages** in your repository settings:
   - Go to Settings → Pages
   - Under "Source", select "GitHub Actions"

2. **Push to main branch** - The workflow will automatically deploy the landing page

3. **Access your site** - Your landing page will be available at:
   - `https://<username>.github.io/<repository-name>/`

### Manual Deployment

If you need to deploy manually:

1. The GitHub Actions workflow can be triggered manually from the Actions tab
2. Or you can push changes to the `landing/` directory on the `main` branch

## Customization

To customize the landing page:

- Edit `index.html` for content and structure
- Edit `styles.css` for styling and colors
- Edit `script.js` for interactive features

## Local Development

To view the landing page locally:

1. Open `index.html` in a web browser
2. Or use a local server:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js (if you have http-server installed)
   npx http-server -p 8000
   ```
3. Navigate to `http://localhost:8000`

