# nicestlog Documentation

This directory contains the Sphinx-based documentation for nicestlog.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (if available)
uv pip install -r requirements.txt

# Or using the project dependency groups
pip install -e ".[docs]"
```

### Build Commands

```bash
# Build HTML documentation
make html

# Build and serve with auto-reload (development)
make livehtml

# Clean build directory
make clean

# Build from scratch
make clean-build
```

### Alternative Build Methods

Using the build script:
```bash
python ../build_docs.py
```

Using Sphinx directly:
```bash
sphinx-build -b html . _build/html
```

### Development Server

For live editing with auto-reload:
```bash
sphinx-autobuild . _build/html --open-browser
```

## Documentation Structure

```
docs/
├── conf.py                 # Sphinx configuration
├── index.rst              # Main documentation index
├── requirements.txt        # Documentation dependencies
├── Makefile               # Build automation
├── make.bat               # Windows build script
├── _static/               # Static assets (CSS, images)
│   └── custom.css         # Custom styling
├── user_guide/            # User documentation
│   ├── getting_started.md
│   ├── best_practices.md
│   └── advanced_features.md
├── features/              # Feature documentation
│   ├── advanced_assistant.md
│   ├── log_analysis.md
│   └── integrations.md
└── development/           # Developer documentation
    ├── todo.md
    └── api_reference.rst
```

## Features

- **Furo Theme**: Modern, responsive design
- **MyST Parser**: Markdown support with Sphinx extensions
- **Copy Buttons**: Easy code copying
- **Auto-generated API**: Automatic API documentation
- **Custom Styling**: nicestlog-branded appearance
- **Mobile Responsive**: Works on all devices

## Customization

### Theme Configuration

Edit `conf.py` to customize the Furo theme:

```python
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
    },
    # ... more options
}
```

### Custom CSS

Add custom styles to `_static/custom.css`. The file is automatically included via `html_css_files` in `conf.py`.

### MyST Extensions

Enable additional MyST features in `conf.py`:

```python
myst_enable_extensions = [
    "colon_fence",
    "deflist", 
    "dollarmath",
    "fieldlist",
    "html_admonition",
    # ... more extensions
]
```

## Troubleshooting

### Common Issues

**Sphinx not found**
```bash
pip install sphinx
```

**Theme not found**
```bash
pip install furo
```

**MyST parser errors**
```bash
pip install myst-parser
```

**Build fails with import errors**
Make sure nicestlog is installed:
```bash
pip install -e .
```

### Clean Build

If you encounter caching issues:
```bash
make clean
make html
```

## Contributing

When adding new documentation:

1. Use MyST Markdown format (`.md` files)
2. Follow the existing structure
3. Add new pages to the appropriate `toctree` in `index.rst`
4. Test the build locally before committing
5. Update this README if adding new sections

## Output

The built documentation will be in `_build/html/`. Open `_build/html/index.html` in your browser to view the documentation.

For deployment, copy the contents of `_build/html/` to your web server or hosting platform.