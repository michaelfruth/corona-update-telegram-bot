# Telegram Bot for corona updates (Germany)

This is a Telegram bot for Germany that sends corona news (total cases, cases/100k) as soon as the corona case numbers have been updated. The data published by RKI is used, so this bot is limited to Germany.

## Source

The corona cases published by the Robert Koch Institute (RKI) are used.

**Licence**:

Robert Koch-Institut (RKI)<br/>Licence: [dl-de/by-2-0](https://www.govdata.de/dl-de/by-2-0)<br/>
Data: https://npgeo-corona-npgeo-de.hub.arcgis.com

All used URLs to fetch data can be found in `corona.py`. The two URLs are used:

To check whether the data has been updated: https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID,last_update&returnGeometry=false&outSR=4326&f=json

To retrieve the data: https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID,last_update&returnGeometry=false&outSR=4326&f=json
