import urllib.request
import re

def main():
    username = "Neemayg"
    url = f"https://github.com/users/{username}/contributions"
    print(f"Fetching from: {url}")
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8')
        
    # Find total contributions
    total_match = re.search(r'(\d+)\s+contributions?\s+in the last year', html)
    if total_match:
        total_contribs = total_match.group(1)
        print(f"Total Contributions: {total_contribs}")
    else:
        print("Could not find total contributions")
        total_contribs = "0"
        
    # Find tooltips
    # Format: for="contribution-day-component-0-12" popover="manual" data-direction="n" data-type="label" data-view-component="true" class="sr-only position-absolute">1 contribution on November 16th.
    pattern = r'for="contribution-day-component-\d+-(\d+)"[^>]*>([^<]+)'
    matches = re.findall(pattern, html)
    print(f"Found {len(matches)} tooltip matches")
    
    weekly_contributions = [0] * 53
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
            
    print("Weekly contributions:", weekly_contributions)
    print("Max weekly contribution:", max(weekly_contributions))

if __name__ == "__main__":
    main()
