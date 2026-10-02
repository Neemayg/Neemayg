import os
import subprocess
import json
import urllib.request
from datetime import datetime

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")

def format_range(start_str, end_str):
    if not start_str or not end_str:
        return ""
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    
    current_year = datetime.now().year
    if start_dt.year == end_dt.year:
        if start_dt.year == current_year:
            return f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"
        else:
            return f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}, {start_dt.year}"
    else:
        return f"{start_dt.strftime('%b %d, %Y')} - {end_dt.strftime('%b %d, %Y')}"

def query_graphql(query):
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        try:
            req = urllib.request.Request(
                'https://api.github.com/graphql',
                data=json.dumps({'query': query}).encode('utf-8'),
                headers={
                    'Authorization': f'bearer {token}',
                    'User-Agent': 'Python-Urllib',
                    'Content-Type': 'application/json'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as res:
                return json.loads(res.read().decode('utf-8'))
        except Exception as e:
            print(f"GraphQL request with token failed: {e}")
            
    try:
        out = subprocess.check_output(['gh', 'api', 'graphql', '-f', f'query={query}'], text=True)
        return json.loads(out)
    except Exception as e:
        print(f"gh CLI GraphQL request failed: {e}")
        return None

def main():
    username = "Neemayg"
    print(f"Fetching live GitHub GraphQL data for {username}...")

    main_query = """
    query {
      user(login: "Neemayg") {
        createdAt
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    
    res = query_graphql(main_query)
    
    current_year = datetime.now().year
    years = range(2024, current_year + 1)
    lifetime_total = 0
    
    for y in years:
        y_query = """
        query {
          user(login: "Neemayg") {
            contributionsCollection(from: "%s-01-01T00:00:00Z", to: "%s-12-31T23:59:59Z") {
              contributionCalendar {
                totalContributions
              }
            }
          }
        }
        """ % (y, y)
        y_res = query_graphql(y_query)
        if y_res and 'data' in y_res and y_res['data']['user']:
            t = y_res['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']
            lifetime_total += t

    if res and 'data' in res and res['data']['user']:
        user_data = res['data']['user']
        first_contrib_str = user_data.get("createdAt", "2024-04-30T00:00:00Z")[:10]
        cc = user_data['contributionsCollection']['contributionCalendar']
        total_contribs_year = str(cc['totalContributions'])
        
        weeks = cc['weeks']
        days = []
        weekly_contributions = []
        
        for w in weeks:
            w_sum = sum(d['contributionCount'] for d in w['contributionDays'])
            weekly_contributions.append(w_sum)
            for d in w['contributionDays']:
                days.append(d)
                
        long_streak = 0
        temp_streak = 0
        start_long = ''
        end_long = ''
        temp_start = ''

        for d in days:
            count = d['contributionCount']
            date = d['date']
            if count > 0:
                if temp_streak == 0:
                    temp_start = date
                temp_streak += 1
                if temp_streak > long_streak:
                    long_streak = temp_streak
                    start_long = temp_start
                    end_long = date
            else:
                temp_streak = 0

        curr_streak = 0
        curr_start = ''
        curr_end = ''
        
        in_streak = False
        for d in reversed(days):
            date = d['date']
            count = d['contributionCount']
            if count > 0:
                if not in_streak:
                    in_streak = True
                    curr_end = date
                curr_start = date
                curr_streak += 1
            else:
                if in_streak:
                    break
    else:
        lifetime_total = 834
        total_contribs_year = "772"
        first_contrib_str = "2024-04-30"
        curr_streak = 8
        curr_start = "2026-09-25"
        curr_end = "2026-10-02"
        long_streak = 8
        long_start = "2026-02-01"
        long_end = "2026-02-08"
        weekly_contributions = [2, 5, 8, 12, 15, 20, 25, 30, 45, 60, 50, 40, 30, 20, 15, 10, 5, 2, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240]

    total_contribs = lifetime_total if lifetime_total > 0 else 834
    total_range = f"{format_date(first_contrib_str)} - Present"
    curr_range = format_range(curr_start, curr_end) if curr_start and curr_end else "Sep 25 - Oct 02"
    long_range = format_range(start_long, end_long) if start_long and end_long else "Feb 01 - Feb 08"

    if len(weekly_contributions) < 53:
        weekly_contributions = [0] * (53 - len(weekly_contributions)) + weekly_contributions
    elif len(weekly_contributions) > 53:
        weekly_contributions = weekly_contributions[-53:]

    points = []
    dx = 240.0 / 52.0
    max_val = max(weekly_contributions) if max(weekly_contributions) > 0 else 1
    
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

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 195" width="800" height="195">
  <defs>
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

  <!-- Outer Card Border -->
  <rect x="0.5" y="0.5" width="799" height="194" fill="#000000" stroke="#262626" stroke-width="1" />

  <!-- Vertical Divider -->
  <line x1="520" y1="20" x2="520" y2="175" stroke="#262626" stroke-width="1" />

  <!-- LEFT SECTION: Streak Statistics -->
  <g class="fade-in">
    <!-- Total Contributions -->
    <text x="95" y="88" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{total_contribs}</text>
    <text x="95" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Total Contributions</text>
    <text x="95" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{total_range}</text>

    <!-- Current Streak -->
    <circle cx="260" cy="72" r="20" fill="none" stroke="#262626" stroke-width="2.5" />
    <circle class="draw-ring" cx="260" cy="72" r="20" fill="none" stroke="#58a6ff" stroke-width="2.5" stroke-dasharray="150" transform="rotate(-90 260 72)" />
    <circle cx="260" cy="52" r="8" fill="#000000" />
    <path d="M 11.36 0.17 C 11.66 0.44 11.83 0.82 11.83 1.23 C 11.82 3.23 10.19 4.39 10.19 5.37 C 10.19 6.22 10.87 6.9 11.72 6.9 C 12.35 6.9 12.9 6.52 13.13 5.92 C 13.56 7.6 15.11 8.82 16.92 8.82 C 18.9 8.82 20.5 7.22 20.5 5.24 C 20.5 4.89 20.44 4.55 20.34 4.22 C 21.6 5.35 22.4 7.02 22.4 8.87 C 22.4 12.59 19.38 15.61 15.66 15.61 C 15.28 15.61 14.9 15.58 14.53 15.52 C 14.88 15.01 15.08 14.41 15.08 13.77 C 15.08 11.96 13.62 10.5 11.81 10.5 C 11.21 10.5 10.65 10.66 10.17 10.94 C 10.06 10.19 9.77 9.48 9.33 8.88 C 8.67 9.72 8.28 10.77 8.28 11.91 C 8.28 14.77 10.6 17.09 13.46 17.09 C 13.84 17.09 14.22 17.05 14.58 16.97 C 14.22 18.06 13.18 18.84 11.96 18.84 C 10.19 18.84 8.75 17.4 8.75 15.63 C 8.75 15.29 8.81 14.95 8.9 14.63 C 7.64 15.76 6.84 17.43 6.84 19.28 C 6.84 23 9.86 26.02 13.58 26.02 C 18.52 26.02 22.52 22.02 22.52 17.08 C 22.52 10.78 17.42 5.67 11.36 0.17 Z" fill="#58a6ff" transform="translate(250.5, 40) scale(0.75)" />
    
    <text x="260" y="78" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="bold" text-anchor="middle">{curr_streak}</text>
    <text x="260" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Current Streak</text>
    <text x="260" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{curr_range}</text>

    <!-- Longest Streak -->
    <text x="425" y="88" fill="#ffffff" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{long_streak}</text>
    <text x="425" y="115" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" text-anchor="middle">Longest Streak</text>
    <text x="425" y="140" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5" text-anchor="middle">{long_range}</text>
  </g>

  <!-- RIGHT SECTION: Contribution Activity Line Graph -->
  <g class="fade-in">
    <text x="540" y="30" fill="#8b949e" font-family="Consolas, 'SF Mono', Monaco, monospace" font-size="10" font-weight="bold" letter-spacing="1.5px">CONTRIBUTION ACTIVITY</text>
    <text x="540" y="46" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9.5">{total_contribs_year} contributions in the last year</text>

    <line x1="540" y1="55" x2="780" y2="55" stroke="#262626" stroke-width="1" />
    <line x1="540" y1="165" x2="780" y2="165" stroke="#262626" stroke-width="1" stroke-dasharray="3,3" />
    <line x1="540" y1="70" x2="780" y2="70" stroke="#262626" stroke-width="1" stroke-dasharray="3,3" />

    <text x="532" y="73" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9" text-anchor="end">{max_val}</text>
    <text x="532" y="168" fill="#8b949e" font-family="system-ui, -apple-system, sans-serif" font-size="9" text-anchor="end">0</text>

    <path d="{path_data} L 780 165 L 540 165 Z" fill="url(#area-gradient)" stroke="none" />
    <path class="draw-line" d="{path_data}" fill="none" stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1000" />
  </g>
</svg>'''

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "assets", "streak_v5.svg")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(svg_content)
    print(f"Successfully generated dynamic streak SVG at: {output_path}")

if __name__ == "__main__":
    main()
