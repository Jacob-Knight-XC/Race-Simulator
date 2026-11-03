import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import scrapy
from scrapy.utils.project import get_project_settings

from ..enrichment import parse_location_block
from ..items import AthleteItem, MeetItem, RaceItem, TeamItem


class XcSpider(scrapy.Spider):
    """Crawl TFRRS DIII league pages into Teams / Athletes / Races / Meets."""

    name = "xc"
    allowed_domains = ["tfrrs.org"]
    start_urls = ["https://tfrrs.org/leagues/51.html"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_meet_ids: set[str] = set()

    def parse(self, response):
        """Parse the DIII league index into men's and women's team links."""
        for row in response.xpath('//div[@class="col-lg-4"]/table/tbody/tr'):
            cols = row.xpath(".//td")
            if len(cols) < 2:
                continue
            yield from self._emit_team(response, cols[0], "m")
            yield from self._emit_team(response, cols[1], "f")

    def _emit_team(self, response, column, gender):
        link = column.xpath("./a/@href").get()
        name = column.xpath("./a/text()").get()
        if not link or not name:
            return

        parts = link.split("/")
        team_id = parts[-1].replace(".html", "")
        xc_link = "/".join(parts[:-2]) + "/xc/" + parts[-1]

        item = TeamItem(
            team_name=name.strip(),
            team_id=team_id,
            gender=gender,
        )
        yield item
        yield response.follow(xc_link, callback=self.parse_roster)

    def parse_roster(self, response):
        names = response.xpath('//div[@class="col-lg-4 "]/table//a/text()').getall()
        links = response.xpath('//div[@class="col-lg-4 "]/table//a/@href').getall()
        if not links:
            names = response.xpath('//div[@class="col-lg-4"]/table//a/text()').getall()
            links = response.xpath('//div[@class="col-lg-4"]/table//a/@href').getall()

        team_id = response.url.split("/")[-1].replace(".html", "")
        if not links:
            self._log_error(f"{team_id} Has no roster!\n")
            return

        for name, link in zip(names, links):
            if "," not in name:
                continue
            last_name, first_name = [part.strip() for part in name.split(",", 1)]
            try:
                athlete_id = int(link.split("/")[-3])
            except (IndexError, ValueError):
                continue

            yield AthleteItem(
                athlete_id=athlete_id,
                ath_first=first_name,
                ath_last=last_name,
                team_id=team_id,
            )
            yield response.follow(link, callback=self.parse_races)

    def parse_races(self, response):
        try:
            athlete_id = int(response.url.split("/")[-3])
        except (IndexError, ValueError):
            return

        for table in response.xpath('//table[@class="table table-hover xc"]'):
            distance_raw = table.xpath('tr/td[@width="27%"]/text()').get()
            race_time = table.xpath("tr/td/a/text()").get()
            meet_name = table.xpath("thead/tr/th/a/text()").get()
            meet_href = table.xpath("thead/tr/th/a/@href").get()
            meet_date = table.xpath("thead/tr/th/span/text()").get()
            if not distance_raw or not race_time or not meet_name:
                continue

            distance = distance_raw.replace("Dist.", "").strip()
            meet_id = self._meet_id_from_href(meet_href)
            yield RaceItem(
                athlete_id=athlete_id,
                distance=distance,
                race_time=race_time.strip(),
                meet_name=meet_name.strip(),
                meet_date=meet_date,
                meet_id=meet_id,
            )
            if meet_id and meet_href and meet_id not in self.seen_meet_ids:
                self.seen_meet_ids.add(meet_id)
                yield response.follow(
                    meet_href,
                    callback=self.parse_meet,
                    cb_kwargs={"meet_id": meet_id, "meet_name": meet_name.strip()},
                )

    def parse_meet(self, response, meet_id: str, meet_name: str):
        """Pull venue/location from a TFRRS meet results page."""
        date_text = response.xpath(
            '//div[contains(@class,"panel-heading")]//text()'
        ).getall()
        meet_date = None
        for chunk in date_text:
            cleaned = " ".join(chunk.split())
            if re.search(r"[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}", cleaned):
                meet_date = cleaned
                break

        location_nodes = response.xpath(
            '//div[contains(@class,"panel-heading")]//text()'
        ).getall()
        location_text = None
        for chunk in location_nodes:
            if "," in chunk and re.search(r"\b[A-Z]{2}\b", chunk):
                location_text = chunk.strip()
                break
        if location_text is None:
            # Fallback: multi-line address block often appears as one text node.
            for chunk in location_nodes:
                if "\n" in chunk and len(chunk.strip()) > 10:
                    location_text = chunk.strip()
                    break

        venue_name, city, state = parse_location_block(location_text)
        yield MeetItem(
            meet_id=meet_id,
            meet_name=meet_name,
            meet_date=meet_date,
            location_text=location_text,
            venue_name=venue_name,
            city=city,
            state=state,
        )

    @staticmethod
    def _meet_id_from_href(href: Optional[str] = None) -> Optional[str]:
        if not href:
            return None
        path = urlparse(href).path
        match = re.search(r"/results/xc/(\d+)/", path)
        return match.group(1) if match else None

    def _log_error(self, message: str):
        settings = get_project_settings()
        log_path = Path(settings.get("SCRAPE_ERROR_LOG", "scrape_errors.log"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message)
