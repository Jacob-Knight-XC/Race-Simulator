# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from logging.handlers import TimedRotatingFileHandler
from turtle import distance
import scrapy



class TeamItem(scrapy.Item):
    # define the fields for your item here like:
    team_name = scrapy.Field()
    team_id = scrapy.Field()
    gender = scrapy.Field()
    
class AthleteItem(scrapy.Item):
    athlete_id = scrapy.Field()
    ath_first = scrapy.Field()
    ath_last = scrapy.Field()
    team_id = scrapy.Field()
    
class RaceItem(scrapy.Item):
    athlete_id = scrapy.Field()
    distance = scrapy.Field()
    race_time = scrapy.Field()
    meet_name = scrapy.Field()
    meet_date = scrapy.Field()
    