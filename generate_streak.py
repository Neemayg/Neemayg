import os
import urllib.request
import json
import re
from datetime import datetime

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")

def format_range(start_str, end_str):
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    
    # If same year
    if start_dt.year == end_dt.year:
        # Check if current year, in which case we don't display the year, otherwise we display it
        current_year = datetime.now().year
        if start_dt.year == current_year:
            return f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"
        else:
            return f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}, {start_dt.year}"
    else:
        return f"{start_dt.strftime('%b %d, %Y')} - {end_dt.strftime('%b %d, %Y')}"

def main():
    username = "Neemayg"
    
    # 1. Fetch Streak Stats
    streak_url = f"https://streak-stats.demolab.com/?user={username}&type=json"
    print(f"Fetching streak data from: {streak_url}")
    try:
        req = urllib.request.Request(
            streak_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching streak data: {e}")
        # Fallback values if API is down
        data = {
            "totalContributions": 94,
            "firstContribution": "2024-04-30",
            "longestStreak": {"start": "2025-11-24", "end": "2025-11-27", "length": 4},
            "currentStreak": {"start": "2026-08-28", "end": "2026-08-29", "length": 2}
        }
        
    total_contribs = data.get("totalContributions", 0)
    first_contrib_str = data.get("firstContribution", "2024-04-30")
    total_range = f"{format_date(first_contrib_str)} - Present"
    
    curr_streak = data.get("currentStreak", {}).get("length", 0)
    curr_start = data.get("currentStreak", {}).get("start", "2026-08-28")
    curr_end = data.get("currentStreak", {}).get("end", "2026-08-29")
    curr_range = format_range(curr_start, curr_end)
    
    long_streak = data.get("longestStreak", {}).get("length", 0)
    long_start = data.get("longestStreak", {}).get("start", "2025-11-24")
    long_end = data.get("longestStreak", {}).get("end", "2025-11-27")
    long_range = format_range(long_start, long_end)

    # 2. Fetch Contribution Activity Grid HTML
    contribs_url = f"https://github.com/users/{username}/contributions"
    print(f"Fetching contribution activity from: {contribs_url}")
    weekly_contributions = [0] * 53
    total_contribs_year = "0"
    
    try:
        req = urllib.request.Request(
            contribs_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        # Extract total contributions in the last year
        total_match = re.search(r'(\d+)\s+contributions?\s+in the last year', html)
        if total_match:
            total_contribs_year = total_match.group(1)
        else:
            total_contribs_year = str(total_contribs)
            
        # Parse tooltips for weekly contribution values
        pattern = r'for="contribution-day-component-\d+-(\d+)"[^>]*>([^<]+)'
        matches = re.findall(pattern, html)
        if matches:
            for week_idx_str, text in matches:
                week_idx = int(week_idx_str)
                text = text.strip()
                count_match = re.search(r'^(\d+)\s+contribution', text)
                if count_match:
                    count = int(count_match.group(1))
                else:
                    count = 0
                if week_idx < 53:
                    weekly_contributions[week_idx] += count
        else:
            raise ValueError("No tooltip elements found in contributions HTML")
            
    except Exception as e:
        print(f"Error fetching/parsing contribution activity: {e}")
        # Fallback curve array if github block/timeout/sunset
        weekly_contributions = [1, 2, 4, 3, 5, 2, 1, 0, 2, 4, 6, 8, 5, 3, 2, 1, 0, 1, 3, 5, 2, 1, 0, 2, 4, 3, 2, 1, 0, 1, 2, 3, 1, 0, 0, 1, 2, 1, 0, 0, 1, 2, 1, 0, 1, 2, 3, 2, 4, 5, 6, 8, 10]
        total_contribs_year = str(total_contribs)

    # 3. Generate smooth Bezier curve path string
    points = []
    dx = 240.0 / 52.0  # Width of graph is 240 pixels (from X=540 to X=780)
    max_val = max(weekly_contributions) if max(weekly_contributions) > 0 else 1
    
    # Y ranges from 70 (top of graph) to 165 (bottom of graph), height is 95 pixels (increased!)
    for i in range(53):
        x = 540.0 + i * dx
        y = 165.0 - (weekly_contributions[i] / max_val) * 95.0
        points.append((x, y))
        
    path_data = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(52):
        p0 = points[i]
        p1 = points[i+1]
        p_prev = points[i-1] if i > 0 else p0
        p_next = points[i+2] if i < 51 else p1
        
        cp1_x = p0[0] + dx / 3.0
        cp1_y = p0[1] + (p1[1] - p_prev[1]) / 6.0
        
        cp2_x = p1[0] - dx / 3.0
        cp2_y = p1[1] - (p_next[1] - p0[1]) / 6.0
        
        path_data += f" C {cp1_x:.1f} {cp1_y:.1f}, {cp2_x:.1f} {cp2_y:.1f}, {p1[0]:.1f} {p1[1]:.1f}"

    # Generate SVG content
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 195" width="800" height="195">
  <defs>
    <!-- Ice-blue gradient fading to transparent for area under curve -->
    <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#58a6ff" stop-opacity="0.00" />
    </linearGradient>
  </defs>

  <style>
    @keyframes fadeIn {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    @keyframes drawRing {{
      from {{ stroke-dasharray: 0 150; }}
      to {{ stroke-dasharray: 150 0; }}
    }}
    @keyframes drawLineChart {{
      from {{ stroke-dasharray: 0 1000; }}
      to {{ stroke-dasharray: 1000 0; }}
    }}
    .fade-in {{
      animation: fadeIn 0.8s ease forwards;
    }}
    .draw-ring {{
      animation: drawRing 1.2s ease-out forwards;
    }}
    .draw-line {{
      animation: drawLineChart 1.5s ease-out forwards;
    }}
  </style>

  <!-- Outer Card Border (no rounded corners, grayscale) -->
  <rect x="0.5" y="0.5" width="799" height="194" fill="#000000" stroke="#262626" stroke-width="1" />

  <!-- Vertical Divider (separating left and right) -->
  <line x1="520" y1="20" x2="520" y2="175" stroke="#262626" stroke-width="1" />

  <!-- LEFT SECTION: Streak Statistics (with decreased font sizes) -->
  <g class="fade-in">
    <!-- Total Contributions -->
    <text x="95" y="88" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{total_contribs}</text>
    <text x="95" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Total Contributions</text>
    <text x="95" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{total_range}</text>

    <!-- Current Streak (with circular ring and flame icon) -->
    <!-- Circular Ring center (260, 72), radius 20 -->
    <circle cx="260" cy="72" r="20" fill="none" stroke="#262626" stroke-width="2.5" />
    <circle class="draw-ring" cx="260" cy="72" r="20" fill="none" stroke="#58a6ff" stroke-width="2.5" stroke-dasharray="150" transform="rotate(-90 260 72)" />
    
    <!-- Mask to prevent the ring line from cutting through the flame -->
    <circle cx="260" cy="52" r="8" fill="#000000" />
    
    <!-- Flame Icon (translated to top center of the ring, scaled down) -->
    <path d="M 11.36 0.17 C 11.66 0.44 11.83 0.82 11.83 1.23 C 11.82 3.23 10.19 4.39 10.19 5.37 C 10.19 6.22 10.87 6.9 11.72 6.9 C 12.35 6.9 12.9 6.52 13.13 5.92 C 13.56 7.6 15.11 8.82 16.92 8.82 C 18.9 8.82 20.5 7.22 20.5 5.24 C 20.5 4.89 20.44 4.55 20.34 4.22 C 21.6 5.35 22.4 7.02 22.4 8.87 C 22.4 12.59 19.38 15.61 15.66 15.61 C 15.28 15.61 14.9 15.58 14.53 15.52 C 14.88 15.01 15.08 14.41 15.08 13.77 C 15.08 11.96 13.62 10.5 11.81 10.5 C 11.21 10.5 10.65 10.66 10.17 10.94 C 10.06 10.19 9.77 9.48 9.33 8.88 C 8.67 9.72 8.28 10.77 8.28 11.91 C 8.28 14.77 10.6 17.09 13.46 17.09 C 13.84 17.09 14.22 17.05 14.58 16.97 C 14.22 18.06 13.18 18.84 11.96 18.84 C 10.19 18.84 8.75 17.4 8.75 15.63 C 8.75 15.29 8.81 14.95 8.9 14.63 C 7.64 15.76 6.84 17.43 6.84 19.28 C 6.84 23 9.86 26.02 13.58 26.02 C 18.52 26.02 22.52 22.02 22.52 17.08 C 22.52 10.78 17.42 5.67 11.36 0.17 Z" fill="#58a6ff" transform="translate(250.5, 40) scale(0.75)" />
    
    <text x="260" y="78" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="bold" text-anchor="middle">{curr_streak}</text>
    <text x="260" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Current Streak</text>
    <text x="260" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{curr_range}</text>

    <!-- Longest Streak -->
    <text x="425" y="88" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{long_streak}</text>
    <text x="425" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Longest Streak</text>
    <text x="425" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{long_range}</text>
  </g>

  <!-- RIGHT SECTION: Contribution Activity Line Graph (No overlaps, increased graph) -->
  <g class="fade-in">
    <!-- Header Title (Consolas, Y=30) -->
    <text x="540" y="30" fill="#8b949e" font-family="Consolas, 'SF Mono', Monaco, monospace" font-size="10" font-weight="bold" letter-spacing="1.5px">CONTRIBUTION ACTIVITY</text>
    
    <!-- Subtitle (Placed directly below title at Y=46, left aligned, eliminating overlap) -->
    <text x="540" y="46" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5">{total_contribs_year} contributions in the last year</text>

    <!-- Horizontal divider under headers at Y=55 -->
    <line x1="540" y1="55" x2="780" y2="55" stroke="#262626" stroke-width="1" />

    <!-- Grid / Axis Baseline (dashed, Y=165) -->
    <line x1="540" y1="165" x2="780" y2="165" stroke="#262626" stroke-width="1" stroke-dasharray="3,3" />
    
    <!-- Grid Top Line (dashed, Y=70) -->
    <line x1="540" y1="70" x2="780" y2="70" stroke="#262626" stroke-width="1" stroke-dasharray="3,3" />

    <!-- Y-Axis Labels -->
    <text x="532" y="73" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9" text-anchor="end">{max_val}</text>
    <text x="532" y="168" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9" text-anchor="end">0</text>

    <!-- Area under the curve (Ice-blue gradient fill, Y ends at 165) -->
    <path d="{path_data} L 780 165 L 540 165 Z" fill="url(#area-gradient)" stroke="none" />

    <!-- Line Chart Path (Ice-blue stroke) -->
    <path class="draw-line" d="{path_data}" fill="none" stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1000" />
  </g>
</svg>'''

    output_path = "/Users/neemaysmac/Desktop/Github_Profile/assets/streak_v5.svg"
    with open(output_path, "w") as f:
        f.write(svg_content)
    print(f"Generated unified streak SVG at: {output_path}")

if __name__ == "__main__":
    main()
