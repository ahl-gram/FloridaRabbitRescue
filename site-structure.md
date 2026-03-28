# Florida Rabbit Rescue Directory — Site Structure

## Overview

A static informational website built on GitHub Pages + Netlify.  
Primary audience: Florida residents considering adopting a rabbit, or looking to support rabbit rescue.  
Secondary audience: The rescue organizations themselves.  
Tone: Warm, credible, educational. Not preachy. Visitor-first.

---

## Domain

Suggested options (check availability):
- `floridarabbitrescues.org` (preferred)
- `floridarabbitdirectory.org`
- `flbunnyrescue.org`

Register via Namecheap or Google Domains. Connect to Netlify DNS.

---

## Pages

### 1. Home (`/`)

**Purpose:** Orient the visitor quickly. Answer "what is this and why does it exist?"

**Sections:**
- Hero: Brief headline + one-sentence description of the site's purpose
- Three-column intro cards linking to the three main sections:  
  - "Find a Rescue" → `/directory`  
  - "Before You Adopt" → `/before-you-adopt`  
  - "Rabbit Values" → `/values`
- Brief "About This Directory" paragraph — who maintains it, how it's verified, last updated date
- Footer with contact link and social media icons

---

### 2. Directory (`/directory`)

**Purpose:** The core of the site. List all 9 verified Florida rabbit rescue organizations.

**Sections:**
- Introductory note (2–3 sentences): what the directory includes, how organizations were selected, when it was last verified
- Disclaimer: scoring/ranking note — we do not rank rescues; objective facts only
- Filter bar (optional, can be added later): filter by region of Florida
- Rescue cards — one per organization, in order by years active (longest first)
  - Each card displays:
    - Organization name + location
    - Geographic service area
    - Mission statement (verbatim)
    - 501(c)(3) status + EIN (where confirmed)
    - Year founded / years active
    - Board of Directors verifiability status
    - Link to their website
    - "Last verified" date
- Closed / excluded organizations note at bottom
- "Is your organization missing or incorrect?" — link to correction form (`/contact`)

---

### 3. Shared Values (`/values`)

**Purpose:** Educate visitors on the philosophy behind responsible rabbit rescue and ownership, drawn from House Rabbit Society (houserabbit.org) and rabbit.org Foundation.

**Sections:**
- Brief intro: who HRS and rabbit.org are, and the Marinell Harriman connection
- Disclaimer: rabbit.org Foundation is independent and has no formal affiliation with House Rabbit Society
- Shared values grid — 12 values, each tagged HRS / rabbit.org / Both, with source quotes
- Links to both organizations' philosophy pages
- Closing note: "We encourage you to read both organizations' full philosophy statements before adopting."

---

### 4. Before You Adopt (`/before-you-adopt`)

**Purpose:** Gently but honestly prepare prospective rabbit owners. This is where the HRS/rabbit.org values become practical guidance.

**Sections:**
- "Is a rabbit right for you?" — honest overview (10+ year commitment, cost, care needs)
- What rabbits need — indoor housing, diet, space, enrichment, veterinary care, companionship
- Common misconceptions — rabbits as "starter pets," Easter rabbits, outdoor hutches
- The case for adoption over purchase — link to directory
- External resources:
  - houserabbit.org (care guides)
  - rabbit.org (care and behavior)
  - Links to Florida rabbit-savvy veterinarians (future addition)

---

### 5. About (`/about`)

**Purpose:** Establish credibility and transparency about who runs this site and why.

**Sections:**
- Who maintains this directory and their motivation
- How organizations are selected and verified
- How often information is updated
- Relationship to HRS and rabbit.org (informational; not officially affiliated with either)
- Contact / corrections link

---

### 6. Contact / Corrections (`/contact`)

**Purpose:** Allow rescues or visitors to submit corrections, additions, or general inquiries.

**Sections:**
- Short intro: "If you represent a rescue organization listed here and need to update your information, or if you believe an organization is missing, please use this form."
- Netlify form with fields:
  - Name
  - Email
  - Organization name (if applicable)
  - Type of inquiry: [ Update existing listing | Add new organization | General question | Other ]
  - Message / details
  - Submit button
- Response time note: "We aim to review all submissions within 2–4 weeks."

---

## Navigation

Primary nav (top): Home · Directory · Values · Before You Adopt · About  
Secondary nav (footer): Home · Directory · Values · Before You Adopt · About · Contact  
Footer also includes: Last updated date · Links to HRS and rabbit.org · Social media icons

---

## Technical Notes for Claude Code

- Static site — no database required at this stage
- Netlify handles form submissions natively (no backend needed for `/contact`)
- All data lives in a structured data file (see `directory-data.json`) — cards are rendered from this file so updates only require editing data, not HTML
- Mobile-first responsive design
- Target: fast load, accessible, no unnecessary JavaScript
- Analytics: Netlify Analytics or Plausible (privacy-friendly, no cookie banner needed)
- Future additions: region filter on directory, Florida rabbit-savvy vet listings, seasonal content (Easter campaign page)
