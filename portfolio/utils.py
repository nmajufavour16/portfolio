import requests
from django.core.cache import cache
from django.conf import settings

GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'

CONTRIBUTIONS_QUERY = """
query($username: String!) {
    user(login: $username) {
        contributionsCollection {
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        date
                        contributionCount
                    }
                }
            }
        }
"""
def get_github_contributions(username, cache_hours=6):
    cache_key = f'github_contributions_{username}'
    cached = cache.get(cache_key)
    if cached is not None:
        return None
    
    token = getattr(settings, 'GITHUB_TOKEN', None)
    if not token:
        return None
    
    try:
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"username": username}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        cache.set(cache_key, calendar, timeout=cache_hours * 60 * 60)
        return calendar
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None
    
def get_visit_count():
    key = 'site_visit_count'
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=None)
        return 1
    
def group_skills_by_category(skills_queryset):
    grouped = {}
    for skill in skills_queryset:
        grouped.setdefault(skill.category, []).append(skill)
    return grouped