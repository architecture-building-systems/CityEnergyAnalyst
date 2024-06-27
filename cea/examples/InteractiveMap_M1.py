import folium

# Create a base map centered around New York City
map_nyc = folium.Map(location=[40.7128, -74.0060], zoom_start=14)

# Sample data: coordinates for a few buildings
buildings = [
    {'name': 'Empire State Building', 'coordinates': [40.748817, -73.985428]},
    {'name': 'One World Trade Center', 'coordinates': [40.712743, -74.013379]},
    {'name': 'Chrysler Building', 'coordinates': [40.751621, -73.975502]}
]

# Add markers to the map for each building with tooltips
for building in buildings:
    folium.Marker(
        location=building['coordinates'],
        tooltip=building['name'],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(map_nyc)

# Save and display the map
map_nyc.save('NYC_buildings_with_tooltips.html')
