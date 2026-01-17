# FM Stories - Development TODO

*Last updated: January 17, 2026*

---

## Immediate Priorities (Next Session)

Pre-deployment checklist:

- [ ] Test all navigation links (home, about, prev/next, back to articles)
- [ ] Verify mobile responsiveness on actual phone
- [ ] Proofread all 6 articles for typos
- [ ] Test 404 page by visiting invalid URLs
- [ ] Check reading time accuracy on a few articles
- [ ] Verify excerpts display correctly (no cut-off mid-word)
- [ ] Test on different browsers (Chrome, Firefox, Safari)

---

## Deployment Tasks (Session 3)

Getting the site live on the internet:

- [ ] Research hosting platforms:
  - PythonAnywhere (free tier, good for Flask)
  - Render (free tier, auto-deploy from GitHub)
  - Heroku (paid now, but familiar)
  - Railway (simple, free tier available)
- [ ] Choose hosting platform
- [ ] Create hosting account
- [ ] Configure deployment settings
- [ ] Deploy and test live site
- [ ] Set up SSL certificate (HTTPS) - usually automatic on modern hosts
- [ ] Test all functionality on live site

---

## Custom Domain Setup (Session 4)

If/when adding a custom domain:

- [ ] Research domain registrars (Namecheap, Porkbun, Cloudflare)
- [ ] Choose and purchase domain name
- [ ] Configure DNS settings to point to hosting
- [ ] Update hosting platform with custom domain
- [ ] Verify SSL works with new domain
- [ ] Update any hardcoded URLs in the site

---

## Phase 3 Polish Ideas (Future Enhancements)

### Typography & Readability

- [ ] Fine-tune body font size (currently Bootstrap default)
- [ ] Review line-height on mobile devices
- [ ] Check heading hierarchy consistency (h1 > h2 > h3)
- [ ] Consider custom font (Google Fonts: Inter, Lora, or Merriweather)
- [ ] Add proper text spacing between sections

### Color Scheme

- [ ] Evaluate current blue/purple gradient
- [ ] Option: Morecambe colors (red/white) for team theme
- [ ] Option: Keep neutral for flexibility across saves
- [ ] Test color contrast for accessibility (WCAG AA standard)
- [ ] Consider dark mode toggle (future, requires JavaScript)

### Visual Elements

- [ ] Create and add favicon
  - Tool: favicon.io or realfavicongenerator.net
  - Ideas: football icon, "FM" letters, or "SN" initials
- [ ] Add subtle hover effects on article cards
- [ ] Improve footer styling (currently minimal)
- [ ] Consider header banner image for article pages
- [ ] Add smooth scroll behavior

### Navigation Improvements

- [ ] Add breadcrumb navigation (Home > Article > Part 3)
- [ ] "Back to top" button on long articles
- [ ] Keyboard navigation (arrow keys for prev/next)
- [ ] Active state indicator in navbar

---

## Content Features (Future)

Features to add as blog grows:

- [ ] Search functionality (when article count > 20)
- [ ] Category/tag system (for multiple FM saves)
- [ ] Archive page (articles grouped by date/month)
- [ ] RSS feed for subscribers
- [ ] Social sharing buttons (Twitter, Reddit)
- [ ] Comments system (Disqus or similar - much later)

---

## Technical Improvements (As Skills Develop)

Advanced features requiring more learning:

- [ ] Database integration (SQLite first, PostgreSQL later)
- [ ] Admin panel for content management
- [ ] GitHub Actions for automated deployment
- [ ] Analytics integration (Plausible or simple counter)
- [ ] Image optimization and hosting
- [ ] Markdown support for article writing
- [ ] Automated backup system
- [ ] Caching for better performance

---

## Content Pipeline

Workflow improvements:

- [ ] Create article template file with formatting guidelines
- [ ] Set up image hosting solution (if adding FM screenshots)
- [ ] Document article writing process
- [ ] Create consistent naming convention for files

---

## Learning Goals

Study alongside this project:

- [ ] CSS Grid and Flexbox (for custom layouts)
- [ ] JavaScript basics (for interactive features)
- [ ] SQL and database design
- [ ] RESTful API concepts
- [ ] Web security fundamentals (OWASP top 10)
- [ ] Basic SEO practices
- [ ] Accessibility standards (WCAG guidelines)

---

## Known Issues

Current bugs and limitations:

- [ ] Heading detection may misfire on short paragraphs ending without periods
- [ ] No image support in articles (text only)
- [ ] No draft/published status for articles
- [ ] Articles must be manually ordered by part number
- [ ] No pagination (fine for 6 articles, may need later)

---

## Future Content Ideas

Blog posts and series to write:

- [ ] Part 7: League One campaign begins
- [ ] Part 8+: Continue Morecambe story
- [ ] "Building This Blog" - meta series about the development process
- [ ] Tactical deep-dives (formations, player roles)
- [ ] Transfer market analysis posts
- [ ] Season review summaries
- [ ] Other FM saves to document (new series)

---

## Notes

- Keep commits small and descriptive
- Test locally before pushing
- Back up article text files separately
- Document any workarounds or hacks in code comments
