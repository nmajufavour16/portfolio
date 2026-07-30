import requests
from django.core.cache import cache
from django.conf import settings

GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'

# FIX 1: Added the missing closing brackets to the GraphQL query
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
    }
}
"""

def get_github_contributions(username, cache_hours=6):
    cache_key = f'github_contributions_{username}'
    cached = cache.get(cache_key)
    
    # FIX 2: Return the cached data instead of None
    if cached is not None:
        return cached
    
    token = getattr(settings, 'GITHUB_TOKEN', None)
    if not token:
        print("GitHub token is missing in settings.") # Helpful for debugging
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
        
        # Check if GraphQL returned an error despite a 200 OK status
        if "errors" in data:
            print("GraphQL API Error:", data["errors"])
            return None
            
        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        cache.set(cache_key, calendar, timeout=cache_hours * 60 * 60)
        return calendar
        
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        print(f"Failed to fetch GitHub contributions: {e}")
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
    'css': 'css3',
    'css3': 'css3',
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
}
 
 
def get_tech_icons(skills_queryset):
    icons = []
    for skill in skills_queryset:
        slug = skill.resolved_icon_slug
        if slug:
            icons.append({'name': skill.name, 'slug': slug})
    return icons