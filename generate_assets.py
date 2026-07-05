import os

def create_hero_svg(mode):
    bg_color = "#0D1117" if mode == "dark" else "#F6F8FA"
    text_color = "#C9D1D9" if mode == "dark" else "#24292F"
    accent_color = "#58A6FF" if mode == "dark" else "#0969DA"
    border_color = "#30363D" if mode == "dark" else "#D0D7DE"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_color}" />
      <stop offset="100%" stop-color="{border_color}" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.1" />
    </filter>
  </defs>

  <rect width="800" height="400" fill="url(#bgGrad)" rx="12" />

  <!-- Abstract representations of OCR and NLP -->
  <g transform="translate(100, 100)" filter="url(#shadow)">
    <!-- Document -->
    <rect x="0" y="0" width="120" height="160" rx="8" fill="{bg_color}" stroke="{border_color}" stroke-width="2" />
    <line x1="20" y1="30" x2="100" y2="30" stroke="{border_color}" stroke-width="4" stroke-linecap="round" />
    <line x1="20" y1="50" x2="80" y2="50" stroke="{border_color}" stroke-width="4" stroke-linecap="round" />
    <line x1="20" y1="70" x2="100" y2="70" stroke="{border_color}" stroke-width="4" stroke-linecap="round" />
    <text x="60" y="120" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}" text-anchor="middle">IMG</text>
  </g>

  <!-- Arrow -->
  <path d="M 250 180 L 350 180" stroke="{accent_color}" stroke-width="4" stroke-dasharray="8,8" />
  <polygon points="350,175 360,180 350,185" fill="{accent_color}" />

  <!-- Processing Node -->
  <g transform="translate(400, 140)" filter="url(#shadow)">
    <circle cx="40" cy="40" r="40" fill="{bg_color}" stroke="{accent_color}" stroke-width="4" />
    <text x="40" y="48" font-family="sans-serif" font-size="16" font-weight="bold" fill="{text_color}" text-anchor="middle">OCR</text>
  </g>

  <!-- Arrow -->
  <path d="M 490 180 L 550 180" stroke="{accent_color}" stroke-width="4" />
  <polygon points="550,175 560,180 550,185" fill="{accent_color}" />

  <!-- Corrected Document -->
  <g transform="translate(600, 100)" filter="url(#shadow)">
    <rect x="0" y="0" width="120" height="160" rx="8" fill="{bg_color}" stroke="{accent_color}" stroke-width="2" />
    <line x1="20" y1="30" x2="100" y2="30" stroke="{accent_color}" stroke-width="4" stroke-linecap="round" />
    <line x1="20" y1="50" x2="90" y2="50" stroke="{accent_color}" stroke-width="4" stroke-linecap="round" />
    <line x1="20" y1="70" x2="100" y2="70" stroke="{accent_color}" stroke-width="4" stroke-linecap="round" />
    <text x="60" y="120" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}" text-anchor="middle">TEXT</text>
  </g>

  <!-- Text -->
  <text x="400" y="320" font-family="sans-serif" font-size="32" font-weight="bold" fill="{text_color}" text-anchor="middle">End-to-End NLP &amp; OCR</text>
  <text x="400" y="350" font-family="sans-serif" font-size="16" fill="{text_color}" opacity="0.8" text-anchor="middle">High-accuracy text extraction with grammar correction.</text>
</svg>
"""
    with open(f"docs/assets/hero-{mode}.svg", "w") as f:
        f.write(svg)

create_hero_svg("light")
create_hero_svg("dark")
print("SVGs created.")
