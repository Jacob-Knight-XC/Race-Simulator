import scrapy


class TeamItem(scrapy.Item):
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
    meet_id = scrapy.Field()


class MeetItem(scrapy.Item):
    meet_id = scrapy.Field()
    meet_name = scrapy.Field()
    meet_date = scrapy.Field()
    location_text = scrapy.Field()
    venue_name = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
