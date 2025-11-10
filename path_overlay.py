#!/usr/bin/env python3
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json

def parse_gpx_coordinates(gpx_content):
    """Extract coordinates from GPX content"""
    try:
        root = ET.fromstring(gpx_content)
        
        # Handle GPX namespace
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        
        coordinates = []
        
        # Look for track points in tracks
        for trkpt in root.findall('.//gpx:trkpt', ns):
            lat = float(trkpt.get('lat'))
            lon = float(trkpt.get('lon'))
            coordinates.append([lat, lon])
        
        # Also check for waypoints
        for wpt in root.findall('.//gpx:wpt', ns):
            lat = float(wpt.get('lat'))
            lon = float(wpt.get('lon'))
            coordinates.append([lat, lon])
        
        return coordinates
    except Exception as e:
        print(f"Error parsing GPX: {e}")
        return []

def generate_html_map(paths_by_year, output_file, month_day):
    """Generate interactive HTML map"""
    
    # Calculate map center from all coordinates
    all_coords = []
    for year, coords in paths_by_year.items():
        all_coords.extend(coords)
    
    if not all_coords:
        print("❌ No coordinates found!")
        return
    
    center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
    center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)
    
    # Color palette for different years - bright, high contrast colors
    colors = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF',
        '#00FFFF', '#FF8800', '#8800FF', '#FF0088', '#00FF88',
        '#88FF00', '#0088FF', '#FF6600', '#6600FF', '#FF0066'
    ]
    
    # Create JavaScript arrays for paths
    polylines_js = []
    legend_items = []
    
    for i, (year, coords) in enumerate(paths_by_year.items()):
        if not coords:
            continue
            
        color = colors[i % len(colors)]
        
        # Create polyline coordinates string
        coords_str = ', '.join(f'[{lat}, {lon}]' for lat, lon in coords)
        
        polylines_js.append(f"""
        // Path for {year}
        var path{year} = L.polyline([{coords_str}], {{
            color: '{color}',
            weight: 5,
            opacity: 0.9
        }}).addTo(map).bindPopup('{year}: {len(coords)} points');
        
        // Add zoom-dependent styling
        map.on('zoomend', function() {{
            var zoom = map.getZoom();
            var weight = zoom < 10 ? 8 : (zoom < 13 ? 5 : 3);
            path{year}.setStyle({{ weight: weight }});
        }});
        """)
        
        legend_items.append(f'<div><span style="color: {color}; font-weight: bold; font-size: 20px;">■</span> {year} ({len(coords)} points)</div>')
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Year Path Overlay - {month_day}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        .legend {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
        }}
        .legend h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        .legend div {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .info {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <h3>Paths for {month_day}</h3>
        {''.join(legend_items)}
    </div>
    <div class="info">
        <strong>Date:</strong> {month_day}<br>
        <strong>Years with Data:</strong> {len(paths_by_year)}<br>
        <strong>Total Points:</strong> {len(all_coords)}
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Initialize map
        var map = L.map('map').setView([{center_lat}, {center_lon}], 13);
        
        // Add black & white tile layer (Stamen Toner Lite for light B&W or CartoDB Positron)
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(map);
        
        {''.join(polylines_js)}
        
        // Fit map to all paths
        var allCoords = [{', '.join(f'[{lat}, {lon}]' for lat, lon in all_coords)}];
        if (allCoords.length > 0) {{
            var group = new L.featureGroup();
            {''.join(f'group.addLayer(path{year});' for year in paths_by_year.keys() if paths_by_year[year])}
            map.fitBounds(group.getBounds().pad(0.1));
        }}
    </script>
</body>
</html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Generated: {output_file}")

def main():
    reitti_url = os.getenv('REITTI_URL', 'http://192.168.79.2:8030')
    api_token = os.getenv('REITTI_API_TOKEN')
    start_year = int(os.getenv('START_YEAR', '2012'))
    end_year = int(os.getenv('END_YEAR', '2025'))
    
    if not api_token:
        print("ERROR: REITTI_API_TOKEN not set")
        return
    
    # Use today's date (or override with TARGET_DATE env var)
    target_date_str = os.getenv('TARGET_DATE')
    if target_date_str:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    else:
        target_date = datetime.now()
    
    month_day = target_date.strftime('%m-%d')
    
    print(f"🗺️  Reitti Multi-Year Path Overlay Generator")
    print(f"Reitti URL: {reitti_url}")
    print(f"Target Date: {month_day} (across years {start_year}-{end_year})")
    print(f"Years: {start_year}-{end_year}")
    print()
    
    # Fetch paths for this date across years
    headers = {'X-API-TOKEN': api_token}
    paths_by_year = {}
    
    for year in range(start_year, end_year + 1):
        date_str = f"{year}-{month_day}"
        print(f"  Fetching {date_str}...")
        
        gpx_url = f"{reitti_url}/api/v1/gpx/export"
        params = {'start': date_str, 'end': date_str}
        
        try:
            response = requests.get(gpx_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                coordinates = parse_gpx_coordinates(response.text)
                if coordinates:
                    paths_by_year[year] = coordinates
                    print(f"    ✅ {len(coordinates)} points")
                else:
                    print(f"    ❌ No coordinates parsed")
            else:
                print(f"    ❌ No data ({len(response.content)} bytes)")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    if not paths_by_year:
        print(f"\n❌ No path data found for {month_day} in any year from {start_year}-{end_year}!")
        print(f"   This might be because you didn't have location tracking on {month_day} for these years.")
        return
    
    # Generate HTML map
    output_file = f"/output/path_overlay_{month_day}_{start_year}-{end_year}.html"
    generate_html_map(paths_by_year, output_file, month_day)
    
    print(f"\n🎉 Success! Generated overlay for {month_day} with {len(paths_by_year)} years of data")
    print(f"📁 Output: {output_file}")

if __name__ == '__main__':
    main()