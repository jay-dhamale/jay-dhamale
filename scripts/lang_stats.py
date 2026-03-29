import requests
import os

TOKEN = os.getenv("GH_TOKEN")
ORG_LIST = os.getenv("ORG_LIST", "").split(",")

headers = {"Authorization": f"token {TOKEN}"}

language_totals = {}

def fetch_all_pages(url):
    results = []
    page = 1
    while True:
        res = requests.get(f"{url}?per_page=100&page={page}", headers=headers).json()
        if not res:
            break
        results.extend(res)
        page += 1
    return results

def add_languages(repo):
    if repo.get("fork"):
        return
    langs = requests.get(repo["languages_url"], headers=headers).json()
    for lang, bytes_ in langs.items():
        language_totals[lang] = language_totals.get(lang, 0) + bytes_

# 🔹 Personal repos
repos = fetch_all_pages("https://api.github.com/user/repos")
for repo in repos:
    add_languages(repo)

# 🔹 Org repos
for org in ORG_LIST:
    if not org:
        continue
    org_repos = fetch_all_pages(f"https://api.github.com/orgs/{org}/repos")
    for repo in org_repos:
        add_languages(repo)

# 🔹 Convert to %
total = sum(language_totals.values())
percentages = {
    lang: round((val / total) * 100, 2)
    for lang, val in language_totals.items()
}

# 🔹 Sort
sorted_langs = sorted(percentages.items(), key=lambda x: x[1], reverse=True)

# 🔹 Generate markdown
md = "## 🧠 Language Usage (All Repos + Orgs)\n\n"
md += "| Language | % |\n|----------|---|\n"

for lang, pct in sorted_langs:
    md += f"| {lang} | {pct}% |\n"

# 🔹 Replace section in README
with open("README.md", "r") as f:
    content = f.read()

start = "<!-- LANG_STATS_START -->"
end = "<!-- LANG_STATS_END -->"

new_section = f"{start}\n{md}\n{end}"

import re
updated = re.sub(f"{start}.*?{end}", new_section, content, flags=re.DOTALL)

with open("README.md", "w") as f:
    f.write(updated)
