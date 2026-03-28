# Florida Rabbit Rescue Directory — Launch Checklist

A step-by-step sequence for getting the site live and building an audience.  
Work through these in order — each phase builds on the last.

---

## Phase 1 — Foundation (Before Writing a Line of Code)

- [ ] **Register your domain name**
  - Check availability: `floridarabbitrescues.org`, `floridarabbitdirectory.org`, `flbunnyrescue.org`
  - Register via Namecheap or Google Domains
  - Register as early as possible — domain names get taken fast
  - Set a calendar reminder for annual renewal
  - Tip: register the `.org` version — it signals nonprofit intent to visitors

- [ ] **Set up a dedicated email address for the project**
  - Something like `hello@floridarabbitrescues.org` or `directory@floridarabbitrescues.org`
  - Use this for all rescue outreach — keeps it separate from personal email
  - Google Workspace (~$6/month) or Zoho Mail (free tier) both connect to custom domains

- [ ] **Create a GitHub account** (if you don't already have one)
  - This is where the site's code will live
  - Free for public repositories

- [ ] **Create a Netlify account**
  - Free tier is sufficient
  - Connect to your GitHub account during setup

---

## Phase 2 — Rescue Outreach (Run Parallel to Site Build)

- [ ] **Draft your outreach email** *(see outreach-email.md in this folder)*

- [ ] **Find contact information for each of the 9 organizations**
  - GRR: gainesvillerabbitrescue.org/contact-us/
  - ORCA: orlandorabbit.org/contact-us
  - TBHRR: tbhrr.org (contact form)
  - SWFL HRR: respectforrabbits.org
  - ECRR: eastcoastrabbitrescue.org/contact-us/
  - Penny & Wild: pennyandwild.org/about-us/contact-us/
  - Space Coast Bunnies: via Facebook or Linktree email link
  - Bebette's: bebettesbunnyrescue.org (contact form)
  - Holly Hops: hollyhops.org/contact-us

- [ ] **Send outreach emails — one per organization**
  - Log the date sent for each
  - Give a 3-week response window before following up

- [ ] **Track responses** — create a simple spreadsheet:
  - Organization name | Date contacted | Response received | Changes requested | Incorporated into data

- [ ] **Send one follow-up** to non-responders after 3 weeks

- [ ] **Update `directory-data.json`** with any corrections received before launch

---

## Phase 3 — Site Build (with Claude Code)

- [ ] **Open Claude Code and bring the following files:**
  - `site-structure.md` — page layout and content plan
  - `directory-data.json` — all rescue data, structured and ready to use
  - Documentation from your wife's site build (GitHub Pages + Netlify setup)

- [ ] **Build core pages in this order:**
  1. Home (`/`)
  2. Directory (`/directory`) — rendered from `directory-data.json`
  3. Shared Values (`/values`)
  4. Contact / Corrections (`/contact`) — Netlify form
  5. Before You Adopt (`/before-you-adopt`)
  6. About (`/about`)

- [ ] **Set up Netlify form** on the `/contact` page
  - Netlify handles submissions natively — no backend needed
  - Test the form before launch

- [ ] **Connect domain** to Netlify
  - Follow Netlify's DNS setup instructions
  - Allow 24–48 hours for DNS propagation

- [ ] **Test on mobile** — most visitors will arrive on a phone

- [ ] **Check all outbound links** — verify every rescue website link is live

- [ ] **Add "Last Verified: March 2026"** to directory page footer

---

## Phase 4 — Social Media Setup (Same Day as Site Launch)

- [ ] **Create Facebook Page**
  - Page name: "Florida Rabbit Rescue Directory" (or your chosen site name)
  - Category: "Website" or "Education"
  - Add profile photo and cover image (rabbit-related, not copyrighted)
  - Add website URL in bio
  - Write a brief "About" description
  - Pin a welcome post explaining what the page is

- [ ] **Create Instagram account**
  - Same name as Facebook Page for consistency
  - Link to website in bio
  - Cross-post from Facebook for now — don't maintain separately at first

- [ ] **Link Facebook and Instagram** via Meta Business Suite
  - This allows cross-posting with one click

---

## Phase 5 — Soft Launch

- [ ] **Email all 9 rescue organizations** to let them know the site is live
  - Include their direct card link
  - Thank those who responded to outreach
  - Remind all of them of the `/contact` form for corrections

- [ ] **Share the site in 3–5 relevant Florida Facebook groups**
  - Search for: "Florida Rabbit Owners," "Florida Bunny Rescue," county-specific pet groups
  - Write a short, genuine post — not promotional. Explain what it is and why you built it.
  - Don't spam — one post per group, spaced out over a week

- [ ] **Ask friendly rescues to share or link to the site**
  - ORCA, TBHRR, and GRR are the most established and most likely to engage
  - A link from their website to yours is valuable for Google visibility

- [ ] **Create a shareable badge/graphic** for rescues to use
  - Simple text: "Listed on the Florida Rabbit Rescue Directory"
  - Offer it as a PNG or SVG they can add to their own site

---

## Phase 6 — Ongoing Content Rhythm

### Monthly
- [ ] One "rescue spotlight" post — feature one of the 9 organizations
- [ ] Check that all 9 rescue websites are still live and active

### Weekly
- [ ] One educational post on Facebook (cross-post to Instagram)
  - Draw from HRS and rabbit.org shared values for topics
  - Example topics:
    - "Why rabbits aren't good starter pets for children"
    - "What 16 square feet of living space actually looks like for a rabbit"
    - "The 10-year commitment — what rabbit ownership really means"
    - "Why Easter rabbits end up abandoned"
    - "Indoor vs. outdoor: why outdoor hutches put rabbits at risk"

### Seasonally
- [ ] **February–March (pre-Easter):** Run an Easter rabbit awareness campaign
  - This is the highest-impact seasonal content opportunity
  - "Adopt don't shop" messaging
  - Share rescue adoption links
- [ ] **January:** Update "last verified" date on directory; re-verify all listings
- [ ] **As needed:** Add new organizations if they are found and verified

---

## Phase 7 — Future Growth (12+ months)

- [ ] **Expand directory** beyond Florida if interest and capacity allows
- [ ] **Add Florida rabbit-savvy veterinarian listings** — a frequently requested resource
- [ ] **Explore formal partnership** with one or more listed rescue organizations
- [ ] **Consider a newsletter** (Mailchimp free tier) for people who want updates
- [ ] **Apply for a Google Ad Grant** — nonprofits and informational sites can qualify for free Google Ads; this would significantly increase visibility

---

## Reference Files in This Folder

| File | Purpose |
|------|---------|
| `site-structure.md` | Full page-by-page site layout for Claude Code |
| `directory-data.json` | All 9 rescue organizations, structured data |
| `outreach-email.md` | Template email to send to each rescue |
| `launch-checklist.md` | This file |
