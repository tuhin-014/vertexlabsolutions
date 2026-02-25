# VertexLab Solutions Website

Simple landing page for showcasing mobile apps.

## Deployment Options

### Option 1: GitHub Pages (Free)
```bash
# Push to GitHub, then go to Settings > Pages
# Source: main branch, / (root)
# Your site: https://tuhin-014.github.io/vertexlabsolutions/
```

### Option 2: Cloudflare Pages (Free)
1. Connect GitHub to Cloudflare Pages
2. Select this repository
3. Build command: (empty)
4. Output directory: ./
5. Your site: https://vertexlabsolutions.com

### Option 3: Upload to Existing Domain
Since you already own **vertexlabsolutions.com** on Cloudflare:

1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to **Pages** > **Create a site**
4. Connect your GitHub or upload files directly
5. Or use **Workers** for more control

## Customization

### Update App Links
Edit `index.html` and find the app cards. Update the `href` links:
```html
<a href="https://apps.apple.com/..." class="app-link ios">App Store</a>
<a href="https://play.google.com/..." class="app-link android">Play Store</a>
```

### Update Social Links
Find the social section:
```html
<a href="https://x.com/yourhandle" class="social-link">X</a>
```

### Update Support Email
```html
<a href="mailto:support@vertexlabsolutions.com">support@vertexlabsolutions.com</a>
```

## Files
- `index.html` - Main website (single file, no dependencies)
