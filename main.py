from scraping.scraper import Ncaa
import time

if __name__ == "__main__":
    start_time = time.time()
    nc = Ncaa()
    school_ids = nc.school_id_grabber()
    stats = nc.stats(school_ids)
    print(stats)
    print("--- %s seconds ---" % (time.time() - start_time))


