osmosis --read-xml file="centre.osm" --bounding-box top=47.547 left=0.388 bottom=47.196 right=1.066 clipIncompleteEntities=true --write-xml file="agglo-tours.osm"
osmosis --read-xml file="agglo-tours.osm" --tag-filter accept-nodes highway=bus_station,bus_stop,platform --tag-filter reject-relations --tag-filter reject-ways --write-xml file="agglo-tours.bus.osm"
osmosis --read-xml file="agglo-tours.osm" --tag-filter accept-nodes highway=* --tag-filter reject-relations --tag-filter reject-ways --write-xml file="agglo-tours.routes.osm"
http://downloads.cloudmade.com/europe/western_europe/france/centre/centre.osm.bz2
