# Adding New Tools to Photoroom Tools Suite

This guide explains how to add new tools to your Photoroom Tools navigation system.

## 🚀 Quick Start

1. **Edit `tools_config.py`** - Add your new tool configuration
2. **Deploy your tool** - Host it on Railway, Render, or any platform
3. **Update navigation** - Your tool will automatically appear in the nav bar

## 📝 Adding a New Tool

### Step 1: Edit `tools_config.py`

Add your new tool to the `tools` array in `tools_config.py`:

```python
{
    "name": "Your Tool Name",
    "icon": "fas fa-your-icon", 
    "url": "https://your-tool-url.com/",
    "active": True,
    "description": "Brief description of what your tool does"
}
```

### Step 2: Tool Configuration Options

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Display name in navigation |
| `icon` | ✅ | FontAwesome icon class |
| `url` | ✅ | Tool's URL (use `#` for current page) |
| `active` | ❌ | Set to `False` to hide from navigation |
| `description` | ❌ | Tool description (for future use) |

### Step 3: Icon Selection

Use FontAwesome icons. Common options:
- `fas fa-edit` - Editor
- `fas fa-image` - Image tools
- `fas fa-video` - Video tools
- `fas fa-music` - Audio tools
- `fas fa-download` - Download tools
- `fas fa-upload` - Upload tools

## 🌐 Deployment Options

### Option 1: Separate Deployments (Current Setup)
- Each tool is deployed independently
- Tools link to each other via navigation
- Easy to maintain and scale

### Option 2: Single Application (Future)
- All tools in one Flask app
- Shared navigation and styling
- More complex but unified experience

## 📋 Example: Adding a Video Editor

```python
{
    "name": "Video Editor",
    "icon": "fas fa-edit",
    "url": "https://your-video-editor.onrender.com/",
    "active": True,
    "description": "Edit and enhance your videos with AI-powered tools"
}
```

## 🔧 Advanced: Creating a Unified Tool Suite

If you want to combine all tools into one application:

1. **Create a main Flask app** with multiple routes
2. **Use subdirectories** for each tool
3. **Shared navigation** across all tools
4. **Single deployment** for everything

Example structure:
```
photoroom-tools/
├── app.py                 # Main Flask app
├── tools_config.py        # Tool configuration
├── templates/
│   ├── base.html         # Shared layout
│   ├── adlocalizer.html  # AdLocalizer tool
│   ├── converter.html    # Video converter tool
│   └── editor.html       # Video editor tool
└── static/               # Shared assets
```

## 🎯 Best Practices

1. **Consistent branding** - Use same colors and styling
2. **Clear navigation** - Users should know where they are
3. **Cross-linking** - Link related tools together
4. **Responsive design** - Work on all devices
5. **Loading states** - Show progress indicators

## 📞 Support

When adding new tools:
- Test navigation links work correctly
- Ensure external links open in new tabs
- Verify icons display properly
- Check mobile responsiveness 