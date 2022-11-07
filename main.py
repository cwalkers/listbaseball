from scraping.scraper import Ncaa

if __name__ == "__main__":
    nc = Ncaa()
    school_ids = nc.school_id_grabber()
    print(school_ids)
    stats = nc.stats(school_ids)
    print(stats)


