import sqlite3

PODCAST_INSERT = """
    INSERT INTO podcasts 
    (name, summary, date, url, image) VALUES 
    (:name, :summary, :date, :url, :image)
"""

EPISODE_INSERT = """
    INSERT INTO episodes 
    (name, link, summary, date, duration, podcast_id) VALUES 
    (:name, :link, :summary, :date, :duration, :podcast_id)
"""

class PodcastDB():
    def __init__(self):
        self.conn = sqlite3.connect('./temp/podcast.db')
        self.cursor = self.conn.cursor()

        with self.conn:
            self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS podcasts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, 
                summary TEXT, 
                date TEXT, 
                url TEXT, 
                image TEXT );

            CREATE TABLE IF NOT EXISTS episodes(
                name TEXT, 
                link TEXT, 
                summary TEXT, 
                date TEXT, 
                duration TEXT, 
                podcast_id INTEGER, 
                FOREIGN KEY(podcast_id) REFERENCES podcasts(id));
            ''')

    def get_podcast_id(self, podcast):
        self.cursor.execute('SELECT id FROM podcasts WHERE name=:name and url=:url',{'name': podcast.name, 'url':podcast.url})
        ids = self.cursor.fetchall()
        podcast.id = ids[0][0] if ids and ids[0] else None

    def fetch_pocasts(self):
        self.cursor.execute('SELECT id, name, summary, date, url, image FROM podcasts')
        return self.cursor.fetchall()

    def fetch_episodes(self, podcast_id, number):
        self.cursor.execute('SELECT name, date, summary, link, duration FROM episodes WHERE podcast_id=(?)', (podcast_id,))
        return self.cursor.fetchmany(number)

    def fetch_more(self, number):
        return self.cursor.fetchmany(number)

    def check_podcast_url(self, url):
        self.cursor.execute('SELECT id FROM podcasts WHERE url=(?)',(url,))
        return self.cursor.fetchall()

    def insert_podcast(self, podcast):
        with self.conn:
            self.cursor.execute(PODCAST_INSERT, podcast.to_dict())

    def insert_episode(self, pod_id, episode):
        e = episode.to_dict()
        e['podcast_id'] = pod_id
        with self.conn:
            self.cursor.execute(EPISODE_INSERT, e)

    def insert_episodes(self, pod_id, episodes):
        eps = []
        for e in episodes:
            d = e.to_dict()
            d['podcast_id'] = pod_id
            eps.append(d)

        with self.conn:
            self.cursor.executemany(EPISODE_INSERT, eps)

    def insert_new_episodes(self, pod_id, episodes):
        eps = []
        for e in episodes:
            d = e.to_dict()
            d['podcast_id'] = pod_id
            eps.append(d)

        with self.conn:
            self.cursor.execute('''DELETE FROM episodes WHERE podcast_id=(?)''', (pod_id,))       

            self.cursor.executemany(EPISODE_INSERT, eps)


    def delete_podcast(self, id):
        with self.conn:
            self.cursor.execute('DELETE FROM podcasts WHERE id=(?)', (id,))
            self.cursor.execute('DELETE FROM episodes WHERE podcast_id=(?)', (id,))

    def close_all(self):
        self.cursor.close()
        self.conn.close()
