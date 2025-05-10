# pylint: skip-file
regex = '### \[(?<title>.*?)\!\[\].*?\]\((?<url>https?:\/\/.*?)\)'
class SearchService:
    def get_search_url(self, query: str) -> list[str]:
        results = ["vietstock.vn", "vnexpress.net", "dantri.com.vn"]
        return results
