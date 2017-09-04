import shapefile


sf = shapefile.Reader(r'C:\reference-case-open2\baseline\inputs\building-geometry\zone.shp')
shapes = sf.shapes()

e = shapefile.Editor(shapefile=r"C:\reference-case-open2\baseline\inputs\building-geometry\zone.shp")
e.poly(parts=[[[681487.624899998,225951.262899998],[681487.624899998,225976.262899998],[681512.624899998,225976.262899998],[681512.624899998,225951.262899998]]])
e.record("Appended","Polygon")
e.save(r'C:\reference-case-open2\baseline\inputs\building-geometry\zone.shp')
