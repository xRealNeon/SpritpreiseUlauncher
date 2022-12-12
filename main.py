from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
import requests

class SpritpreiseExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class PreferencesEventListener(EventListener):

    def on_event(self, event, extension):
        #print(event.preferences)
        if event.preferences['lat'] == "auto" and event.preferences['long'] == "auto":
            response = requests.get('http://ip-api.com/json/')
            #print(response.json())
            event.preferences['lat'] = response.json()['lat']
            event.preferences['long'] = response.json()['lon']        

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        #print(extension.preferences)
        url = 'https://apim-p-gw02.adac.de/spritpreise/liste/{lat}/{long}?Sorte={type}&UmkreisKm=5&PageSize=5&PageNumber=1&SortiereNach=Preis&SortierRichtung=asc'.format(
            type=extension.preferences['type'], 
            lat=extension.preferences['lat'],
            long=extension.preferences['long']
        )
        
        response = requests.get(url, headers={'Ocp-Apim-Subscription-Key': 'e9216740d3b64ae0bdaf6cff961afc1b'})
        items = []

        if event.get_argument() is None:            
            for station in response.json()['Data']['Tankstellen']:
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                name=str(station['Preis'])+ "€",
                                                description='{} ~ {}, {}'.format(station['Name'], station['Strasse'], station['Ort']),
                                                on_enter=OpenUrlAction('https://www.adac.de/verkehr/tanken-kraftstoff-antrieb/kraftstoffpreise/details/{postcode}-{location}-{name}/{id}/'.format(
                                                    postcode=station['Plz'],
                                                    location=station['Ort'],
                                                    name=station['Name'],
                                                    id=station['PoiId']
                                                ))))
        else:
            try : 
                km = float(event.get_argument())
                litrePrice = response.json()['Data']['Tankstellen'][0]['Preis']
                consumption = float(extension.preferences['consumption'])
                kmPrice = (consumption * litrePrice) / 100
                km = float(event.get_argument())
                price = round(km * kmPrice, 2)

                items.append(ExtensionResultItem(icon='images/icon.png',
                                                name=str(price) + '€',
                                                description='{}€ pro Lieter; {}€ pro Tankinhalt({} Lieter) ; {} Lieter für die Strecke'.format(litrePrice, round(litrePrice * int(extension.preferences['tank']), 2), int(extension.preferences['tank']), (consumption / 100) * km),
                                                on_enter=DoNothingAction()))
            except :
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                name='Bitte gebe eine Zahl ein!',
                                                description='Fehler',
                                                on_enter=DoNothingAction()))            

        return RenderResultListAction(items)    

if __name__ == '__main__':
    SpritpreiseExtension().run()