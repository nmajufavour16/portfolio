import logging
from datetime import date, datetime

import requests
from django.core.cache import cache
from django.conf import settings

from .models import SiteSettings
from django.db.models import F

GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://api.spotify.com/v1/me/player'
logger = logging.getLogger(__name__)

# FIX 1: Added the missing closing brackets to the GraphQL query
CONTRIBUTIONS_QUERY = """
query($username: String!) {
    user(login: $username) {
        login
        url
        contributionsCollection {
            totalCommitContributions
            totalRepositoriesWithContributedCommits
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        date
                        contributionCount
                        contributionLevel
                    }
                }
            }
        }
    }
}
"""

def _current_streak(weeks):
    days = sorted(
        (day for week in weeks for day in week.get('contributionDays', [])),
        key=lambda day: day.get('date', ''),
        reverse=True,
    )
    today = date.today().isoformat()
    if days and days[0].get('date') == today and days[0].get('contributionCount', 0) == 0:
        days = days[1:]

    streak = 0
    for day in days:
        if day.get('contributionCount', 0) <= 0:
            break
        streak += 1
    return streak


def _month_labels(weeks):
    labels = []
    previous_month = None
    for week in weeks:
        for day in week.get('contributionDays', []):
            day_date = day.get('date', '')
            month = day_date[:7]
            if month and month != previous_month:
                labels.append(date.fromisoformat(day_date).strftime('%b'))
                previous_month = month
    return labels[-12:]


def get_github_contributions(username, cache_hours=1):
    normalized_username = username.strip().lower()
    cache_key = f'github_contributions_{normalized_username}'
    stale_cache_key = f'{cache_key}_stale'
    cached = cache.get(cache_key)
    
    # FIX 2: Return the cached data instead of None
    if cached is not None:
        return cached
    
    token = getattr(settings, 'GITHUB_TOKEN', None)
    if not token:
        logger.warning('GITHUB_TOKEN is missing; contribution data cannot be refreshed.')
        return cache.get(stale_cache_key)
    
    try:
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"username": normalized_username}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        
        # Check if GraphQL returned an error despite a 200 OK status
        if "errors" in data:
            logger.warning('GitHub GraphQL API error: %s', data['errors'])
            return cache.get(stale_cache_key)

        user = data['data']['user']
        if user is None:
            return cache.get(stale_cache_key)

        calendar = user['contributionsCollection']['contributionCalendar']
        calendar['username'] = user['login']
        calendar['profileUrl'] = user['url']
        calendar['totalCommits'] = user['contributionsCollection']['totalCommitContributions']
        calendar['totalRepos'] = user['contributionsCollection']['totalRepositoriesWithContributedCommits']
        calendar['currentStreak'] = _current_streak(calendar.get('weeks', []))
        calendar['monthLabels'] = _month_labels(calendar.get('weeks', []))
        cache.set(cache_key, calendar, timeout=cache_hours * 60 * 60)
        cache.set(stale_cache_key, calendar, timeout=7 * 24 * 60 * 60)
        return calendar
        
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        logger.warning('Failed to refresh GitHub contributions: %s', e)
        return cache.get(stale_cache_key)


def get_github_activity(username, cache_hours=1):
    normalized_username = username.strip().lower()
    cache_key = f'github_activity_{normalized_username}'
    stale_cache_key = f'{cache_key}_stale'
    cached = cache.get(cache_key)
    
    if cached is not None:
        return cached
        
    token = getattr(settings, 'GITHUB_TOKEN', None)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Accept"] = "application/vnd.github.v3+json"
    
    try:
        response = requests.get(
            f"https://api.github.com/users/{normalized_username}/events/public",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        events = response.json()
        
        # Parse the 4 most recent meaningful events
        parsed_events = []
        for event in events:
            if len(parsed_events) >= 4:
                break
                
            event_type = event.get('type')
            repo_name = event.get('repo', {}).get('name')
            created_at_str = event.get('created_at')
            created_at = None
            if created_at_str:
                try:
                    # GitHub API uses 'Z' for UTC, replace with '+00:00' for fromisoformat
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            item = {
                'repo': repo_name,
                'created_at': created_at,
                'type': event_type,
                'url': f"https://github.com/{repo_name}"
            }
            
            if event_type == 'PushEvent':
                commits = event.get('payload', {}).get('commits', [])
                item['message'] = commits[0].get('message') if commits else "Pushed to repository"
                item['badge'] = "push"
            elif event_type == 'PullRequestEvent':
                action = event.get('payload', {}).get('action', 'Opened')
                number = event.get('payload', {}).get('number', '')
                item['message'] = f"{action.capitalize()} PR #{number}: {event.get('payload', {}).get('pull_request', {}).get('title', '')}"
                item['badge'] = "pull-request"
            elif event_type == 'IssuesEvent':
                action = event.get('payload', {}).get('action', 'Opened')
                number = event.get('payload', {}).get('issue', {}).get('number', '')
                item['message'] = f"{action.capitalize()} issue #{number}: {event.get('payload', {}).get('issue', {}).get('title', '')}"
                item['badge'] = "issue"
            elif event_type == 'WatchEvent':
                item['message'] = f"Starred {repo_name} repository"
                item['badge'] = "starred"
            elif event_type == 'CreateEvent':
                ref_type = event.get('payload', {}).get('ref_type', 'repository')
                item['message'] = f"Created {ref_type} in {repo_name}"
                item['badge'] = "created"
            else:
                continue # Skip other events for a cleaner feed
                
            parsed_events.append(item)
            
        cache.set(cache_key, parsed_events, timeout=cache_hours * 60 * 60)
        cache.set(stale_cache_key, parsed_events, timeout=7 * 24 * 60 * 60)
        return parsed_events
        
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        logger.warning('Failed to refresh GitHub activity: %s', e)
        return cache.get(stale_cache_key) or []

def _format_spotify_track(item, *, is_playing=False, played_at=None):
    album = item.get('album') or {}
    images = album.get('images') or []
    artists = ', '.join(artist.get('name', '') for artist in item.get('artists', []) if artist.get('name'))
    return {
        'title': item.get('name', ''),
        'artist': artists,
        'album': album.get('name', ''),
        'image_url': images[0].get('url') if images else None,
        'spotify_url': (item.get('external_urls') or {}).get('spotify'),
        'is_playing': is_playing,
        'played_at': played_at,
    }


def get_spotify_listening():
    cache_key = 'spotify_listening_now'
    stale_cache_key = f'{cache_key}_stale'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    client_id = getattr(settings, 'SPOTIFY_CLIENT_ID', None)
    client_secret = getattr(settings, 'SPOTIFY_CLIENT_SECRET', None)
    refresh_token = getattr(settings, 'SPOTIFY_REFRESH_TOKEN', None)
    if not all((client_id, client_secret, refresh_token)):
        return cache.get(stale_cache_key)

    try:
        token_response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={'grant_type': 'refresh_token', 'refresh_token': refresh_token},
            auth=(client_id, client_secret),
            timeout=5,
        )
        token_response.raise_for_status()
        access_token = token_response.json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}

        current_response = requests.get(
            f'{SPOTIFY_API_URL}/currently-playing',
            headers=headers,
            timeout=5,
        )
        if current_response.status_code == 200:
            current = current_response.json()
            item = current.get('item')
            if item and item.get('type') == 'track':
                listening = _format_spotify_track(item, is_playing=bool(current.get('is_playing')))
                cache.set(cache_key, listening, timeout=30)
                cache.set(stale_cache_key, listening, timeout=24 * 60 * 60)
                return listening
        elif current_response.status_code != 204:
            current_response.raise_for_status()

        recent_response = requests.get(
            f'{SPOTIFY_API_URL}/recently-played',
            params={'limit': 1},
            headers=headers,
            timeout=5,
        )
        recent_response.raise_for_status()
        recent_items = recent_response.json().get('items', [])
        if not recent_items:
            return cache.get(stale_cache_key)

        recent = recent_items[0]
        listening = _format_spotify_track(
            recent.get('track') or {},
            is_playing=False,
            played_at=recent.get('played_at'),
        )
        cache.set(cache_key, listening, timeout=60)
        cache.set(stale_cache_key, listening, timeout=24 * 60 * 60)
        return listening
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        logger.warning('Failed to refresh Spotify listening data: %s', exc)
        return cache.get(stale_cache_key)

def get_visit_count():
    settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
    SiteSettings.objects.filter(id=1).update(all_time_visitors=F('all_time_visitors') + 1)
    settings_obj.refresh_from_db()
    return settings_obj.all_time_visitors

def group_skills_by_category(skills_queryset):
    grouped = {}
    for skill in skills_queryset:
        grouped.setdefault(skill.category, []).append(skill)
    return grouped

SIMPLE_ICON_SLUGS = {
    'react': 'react',
    'next.js': 'nextdotjs',
    'nextjs': 'nextdotjs',
    'vite': 'vite',
    'typescript': 'typescript',
    'javascript': 'javascript',
    'node.js': 'nodedotjs',
    'nodejs': 'nodedotjs',
    'python': 'python',
    'html': 'html5',
    'html5': 'html5',
    'css': 'css',
    'css3': 'css',
    'tailwind css': 'tailwindcss',
    'tailwindcss': 'tailwindcss',
    'django': 'django',
    'supabase': 'supabase',
    'postgresql': 'postgresql',
    'github': 'github',
    'git': 'git',
    'redux': 'redux',
    'graphql': 'graphql',
    'docker': 'docker',
    'figma': 'figma',
    'canva': 'canva',
    'vercel': 'vercel',
    'mongo db': 'mongodb',
    'mongodb': 'mongodb',
    'pg admin': 'postgresql',
    'pgadmin': 'postgresql',
}

def get_tech_icons(skills_queryset):
    icons = []
    for skill in skills_queryset:
        slug = skill.resolved_icon_slug
        if slug:
            icons.append({'name': skill.name, 'slug': slug})
    return icons
