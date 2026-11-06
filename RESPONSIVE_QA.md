# Responsive portfolio improvements

Starting point: fetched `origin/main` at `015df38` (the merge of the English/Italian switcher). The feature branch is `codex/responsive-portfolio`.

## Audit findings and fixes

- Navigation links were hidden below 960px. They now form a visible, wrapping second header row, keeping Contact Me and EN/IT together above it. The header can wrap rather than overlap when space is limited.
- Brand, navigation and contact links had undersized touch targets. Controls now have at least 44px touch targets at phone/tablet widths, with keyboard focus indicators.
- The About image retained a 610px height on phones. Natural image dimensions now remove the excess empty space while preserving the complete image.
- Case-study mockup containers forced fixed heights and cropped tablet images. At compact widths the containers and images now follow their natural aspect ratios. Mobile portfolio images also show their complete artwork.
- Six-column process grids and four-column priorities became cramped around 1024px. Compact layouts now use three and two columns respectively; phones use one column for readable descriptions. Expertise and portfolio cards use two columns on tablets and one on phones.
- Mobile sections, cards, visual frames, heading sizes and button wrapping now use a consistent spacing scale. Summary metrics remain in two columns rather than occupying four tall rows.
- Anchor scrolling accounts for the sticky header. Reduced-motion preferences disable smooth scrolling and hover movement; default desktop animations remain intact.

All layout changes are scoped to widths up to 1100px. The existing wide-desktop layout, assets, copy, URLs and translation engine are unchanged. No overflow-hiding rule was added. The only wider-screen change is respecting a visitor's explicit reduced-motion preference.

## Repeatable browser audit

The website itself still has no dependencies or build step. Browser checks use development-only Python packages Playwright and Pillow, plus Chromium. They are already available in the prepared cloud environment. To prepare another development machine:

```sh
python3 -m pip install playwright pillow
python3 -m playwright install chromium
```

From the repository root, start the site:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

In a second terminal, run:

```sh
python3 tests/responsive_audit.py --baseline 015df38
```

If using system Chromium, the script discovers `chromium`; otherwise it uses Playwright's installed browser. An alternate binary can be supplied with `CHROMIUM_PATH`. Optional `--url`, `--baseline` and `--output` arguments select the server, comparison Git ref and generated output location. Reports and screenshots default to `/tmp/portfolio-responsive-audit`, outside the checkout.

The audit covers all four pages in English and Italian at 320, 360, 375, 390, 430, 560, 600, 620, 621, 767, 768, 834, 960, 961, 1024, 1100, 1101, 1280 and 1440px: 152 combinations. It checks document and element overflow, clipped content, overlapping grid/header siblings, visible navigation, 44px touch targets and uncropped case-study mockups.

At 1440px, the audit loads the original baseline CSS and compares every element's geometry plus full-page screenshots in both languages. Screenshot comparison tolerates only channel differences of at most 3/255, accounting for Chromium's rounded-edge antialiasing on reload; geometry must match exactly.

Interaction checks cover keyboard language switching, English first visit despite an Italian browser locale, reload and cross-page preference persistence, back navigation, cross-tab sync, blocked localStorage, sticky-header anchor clearance, reduced motion and landscape orientation.

Additional validation during this change checked all translated text/attribute bindings, page titles, descriptions and alt text against the existing shared dictionary, invalid preferences, and preserved link destinations. JavaScript syntax and Git whitespace checks passed.

## Limits

Validation uses Chromium browser automation and visual review, rather than physical iOS/Android devices or Safari. Research diagrams and interface screenshots contain their original baked-in text; their assets and translations were not altered. No merge, publication or deployment commands are part of this change.
