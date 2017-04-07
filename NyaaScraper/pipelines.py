# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import json
import pyrebase
import re
import os

class NyaascraperPipeline(object):

    def open_spider(self, spider):
        self.tracking = ['Saenai Heroine no Sodatekata', 'Rokudenashi Majutsu Koushi to Akashic Records']
        self.qualities = ['720p']
        self.subbers = ['HorribleSubs']
        self.data = []
        with open('NyaaScraper/firebase.json') as firebase_config:
            firebase_config_json = json.load(firebase_config)
            firebase = pyrebase.initialize_app(firebase_config_json)
            auth = firebase.auth()
            self.db = firebase.database()
            with open('NyaaScraper/auth.json') as auth_config:
                auth_config_json = json.load(auth_config)
                self.user = auth.sign_in_with_email_and_password(auth_config_json["email"], auth_config_json["password"])
                # Get all the animes that are currently in the databse. This is an array of PyreResponse objects.
                self.existing_anime = self.db.child('anime').get().each()

    def close_spider(self, spider):
        for new_data in self.data:
            self.db.child('anime').update(new_data, self.user['idToken'])
            # db.child("users").child("Morty").remove(user['idToken'])

    def process_item(self, item, spider):
        incoming_name = item['name']
        for quality in self.qualities:
            # Check quality of the incoming anime torrent.
            if quality not in incoming_name:
                raise DropItem('Quality %s was not found in %s.' % (quality, item))
            for tracking_subs in self.subbers:
                if tracking_subs in incoming_name:
                    # Strip the extension from the title.
                    title, ext = os.path.splitext(incoming_name)
                    # Get rid of all the brackets with text into them and the whitespaces around them ('[1080p]' and '[Subs]' f.e.).
                    name_episode = re.sub('\s*\[\w+\]\s*', '', title)
                    try:
                        # Split on dash with all the necessary whitespaces between and after.
                        name_and_epi = re.split('\s*-\s*', name_episode)
                        name = name_and_epi[0]
                        # Parse the second episode number to a Integer.
                        epi = int(name_and_epi[1])
                        for anime in self.existing_anime:
                            # Check whether the anime already exists in our database and whether this is a new episode.
                            if name == anime.key() and epi <= anime.val():
                                raise DropItem('Episode number %s already scraped in %s.' % (epi, item))
                        self.data.append({ name : epi })
                        return item
                    except TypeError:
                        raise DropItem('Wrong parsing of episode number in %s.' % item)
            raise DropItem('Not a HorribleSubs episode: %s.' % item)
