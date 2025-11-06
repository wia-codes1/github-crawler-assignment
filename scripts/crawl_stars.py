import os, time, requests, psycopg2
from psycopg2.extras import execute_values

GITHUB_API = "https://api.github.com/graphql"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github.v4+json"}

QUERY = """
query($q:String!, $first:Int!, $after:String) {
  rateLimit { limit cost remaining resetAt }
  search(query: $q, type: REPOSITORY, first: $first, after: $after) {
    pageInfo { endCursor hasNextPage }
    edges {
      node {
        ... on Repository {
          id
          name
          owner { login }
          stargazerCount
          url
          isArchived
        }
      }
    }
  }
}
"""

DB_DSN = os.environ.get("POSTGRES_DSN", "host=postgres port=5432 dbname=postgres user=postgres password=postgres")

def upsert_repos(rows):
    sql = """
    INSERT INTO repo_summary (repo_id, full_name, owner_login, name, stars, html_url, archived)
    VALUES %s
    ON CONFLICT (repo_id) DO UPDATE SET
      stars = EXCLUDED.stars,
      fetched_at = now();
    """
    tuples = [(r['repo_id'], r['full_name'], r['owner'], r['name'], r['stars'], r['url'], r['archived']) for r in rows]
    with psycopg2.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, tuples)
        conn.commit()

def main():
    cursor, total = None, 0
    while total < 100:
        data = requests.post(GITHUB_API,
            json={"query": QUERY, "variables": {"q": "is:public", "first": 10, "after": cursor}},
            headers=HEADERS).json()
        repos = []
        for edge in data["data"]["search"]["edges"]:
            n = edge["node"]
            repos.append({
                "repo_id": int(n["id"].split(":")[-1]) if ":" in n["id"] else n["id"],
                "full_name": f"{n['owner']['login']}/{n['name']}",
                "owner": n['owner']['login'],
                "name": n['name'],
                "stars": n['stargazerCount'],
                "url": n['url'],
                "archived": n['isArchived']
            })
        upsert_repos(repos)
        total += len(repos)
        print(f"Inserted {total}")
        page = data["data"]["search"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
        time.sleep(2)

if __name__ == "__main__":
    main()
