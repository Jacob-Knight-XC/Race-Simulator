import scrapy
from ..items import TeamItem, AthleteItem, RaceItem


class XcSpider(scrapy.Spider):
    
    name = 'xc'
    allowed_domains = ['tfrrs.org']
    start_urls = ['https://tfrrs.org/leagues/51.html']
    
    def start_requests(self):
        for i in self.start_urls:
            yield scrapy.Request(i, callback=self.parse)

    #Data for team table
    def parse(self, response):
        self.d3 = response.xpath('//div[@class="col-lg-4"]/table/tbody/tr')
        male = TeamItem()
        female = TeamItem()
        
        for x in self.d3:
            malecol, femalecol = x.xpath('.//td')
            self.malelink = malecol.xpath('./a/@href').get()
            self.maleteam = malecol.xpath('./a/text()').get()
            
            if self.malelink is not None:
                self.mxclink = self.malelink.split('/')
                self.mxclink = '/'.join(self.mxclink[:-2]) + '/xc/' + self.mxclink[-1]
                team_id = self.malelink.split('/')[-1].replace('.html', '')
                male['team_name'] = self.maleteam
                male['team_id'] = team_id
                male['gender'] = 'm'
            
                yield male
                yield response.follow(self.mxclink, callback=self.parse_athletes)
        
            self.femalelink = femalecol.xpath('./a/@href').get()
            self.femaleteam = femalecol.xpath('./a/text()').get()
            
            if self.femalelink is not None:
                self.fxclink = self.femalelink.split('/')
                self.fxclink = '/'.join(self.fxclink[:-2]) + '/xc/' + self.fxclink[-1]
                team_id = self.femalelink.split('/')[-1].replace('.html', '')
                female['team_name'] = self.femaleteam
                female['team_id'] = team_id
                female['gender'] = 'f'
            
                yield female
                yield response.follow(self.fxclink, callback=self.parse_athletes)
    
    #data for athlete table
    def parse_athletes(self, response):
        athName = response.xpath('//div[@class="col-lg-4 "]/table//a/text()').getall()
        athLink = response.xpath('//div[@class="col-lg-4 "]/table//a/@href').getall()
        team_id = response.url.split('/')[-1].replace('.html', '')
       
        if len(athLink) == 0:
            athName = response.xpath('//div[@class="col-lg-4"]/table//a/text()').getall()
            athLink = response.xpath('//div[@class="col-lg-4"]/table//a/@href').getall()
           
            if len(athLink) == 0:
                self.log_error(team_id + "Has no roster!\n")
      
        for i in range(len(athLink)):
            athlete = AthleteItem()
            name = athName[i]
            last_name, first_name = name.split(',')
            last_name = last_name.strip()
            first_name = first_name.strip()
            splitLink = athLink[i].split('/')
            athID = int(splitLink[-3])

            athlete['athlete_id'] = athID
            athlete['ath_first'] = first_name
            athlete['ath_last'] = last_name
            athlete['team_id'] = team_id
           
            yield athlete
            yield response.follow(athLink[i], callback=self.parse_races)

    #data for races table
    def parse_races(self, response):
        
        self.xcfun = response.xpath('//table[@class="table table-hover xc"]')
        
        for x in self.xcfun:
            items = RaceItem()
            self.athlete_id = response.url.split('/')[-3]
            self.distance = x.xpath('tr/td[@width="27%"]/text()').get()[7:-5]
            self.timing = x.xpath('tr/td/a/text()').get()
            self.meet_name = x.xpath('thead/tr/th/a/text()').get()
            self.meet_date = x.xpath('thead/tr/th/span/text()').get()
            
            items['athlete_id'] = self.athlete_id
            items['distance'] = self.distance
            items['race_time'] = self.timing
            items['meet_name'] = self.meet_name
            items['meet_date'] = self.meet_date
            
            yield items