#!/bin/bash
# deploy-docs.sh

echo "🚀 Deploying GitHub Pages for Self-Arguing Multi-Agent Analyst"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Run this from the project root directory"
    exit 1
fi

# Create docs directory if it doesn't exist
mkdir -p docs

echo "📁 Created docs directory structure"

# Copy README content to docs
echo "📝 Generating documentation..."

# Create a simple index if it doesn't exist
if [ ! -f "docs/index.md" ]; then
    cat > docs/index.md << 'EOF'
---
layout: default
title: Self-Arguing Multi-Agent Analyst
---

# Self-Arguing Multi-Agent Analyst

**Epistemic disagreement as a first-class signal in cybersecurity incident analysis**

> **You don't trust models—you make them earn belief through structured disagreement.**

## Quick Links

- [Architecture](architecture.html) - System design and components
- [API Reference](api.html) - REST endpoints and usage  
- [Design Decisions](decisions.html) - Why we built it this way
- [Experiments](experiments.html) - Results and validation

## Repository

All source code, tests, and deployment configurations are available in the [GitHub repository](https://github.com/mastercaleb254/self-arguing-analyst).

**Live demo**: [api.self-arguing-analyst.com](https://api.self-arguing-analyst.com)

---

*This is documentation-as-a-site. The code remains the engine; this page becomes the dashboard.*
EOF
    echo "✅ Created docs/index.md"
fi

# Enable GitHub Pages
echo "🌐 Enabling GitHub Pages..."

# Instructions for manual setup
cat << 'EOF'

📋 MANUAL SETUP REQUIRED:

1. Go to: https://github.com/mastercaleb254/self-arguing-analyst/settings/pages
2. Under "Source", select:
   - Branch: main
   - Folder: /docs
3. Click "Save"
4. Wait 1-2 minutes for deployment
5. Your site will be live at: https://mastercaleb254.github.io/self-arguing-analyst

OPTIONAL: For custom domain:
1. Add CNAME file to docs/ with your domain
2. Update DNS settings at your registrar
3. Configure in GitHub Pages settings

EOF

# Update README with website link
echo "🔗 Updating README with website link..."
if ! grep -q "## Documentation Website" README.md; then
    cat >> README.md << 'EOF'

## Documentation Website

Live documentation: https://mastercaleb254.github.io/self-arguing-analyst

This website provides:
- Architecture overview
- API reference
- Design decisions
- Experiment results
- Deployment guides

EOF
    echo "✅ Updated README.md"
fi

echo "🎉 Documentation setup complete!"
echo ""
echo "Next steps:"
echo "1. Commit and push changes:"
echo "   git add docs/ README.md"
echo "   git commit -m 'Add GitHub Pages documentation'"
echo "   git push origin main"
echo "2. Enable GitHub Pages in repository settings"
echo "3. Visit: https://mastercaleb254.github.io/self-arguing-analyst"
