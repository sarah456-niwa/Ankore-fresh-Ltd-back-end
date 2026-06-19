import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Ensure project root is on sys.path so `import ankore` works
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ankore.settings')
import django
django.setup()
from products.models import Product

ASSETS_DIR = PROJECT_ROOT.parent / 'Ankore-Fresh-Ltd' / 'assets' / 'images'
MEDIA_ROOT = PROJECT_ROOT / 'media'

os.makedirs(MEDIA_ROOT / 'products', exist_ok=True)

def find_candidate(basename_lower):
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in files:
            if basename_lower in f.lower():
                return Path(root) / f
    return None

copied = 0
not_found = []
for p in Product.objects.all():
    if not p.image:
        continue
    dest_rel = p.image.name  # e.g., products/fresh_mangoes.jpg
    dest_path = MEDIA_ROOT / dest_rel
    if dest_path.exists():
        continue
    basename = os.path.basename(dest_rel)
    key = os.path.splitext(basename)[0].lower().replace('_', ' ').replace('-', ' ')
    # try direct match
    candidate = find_candidate(basename.lower())
    if not candidate:
        # try tokens
        for token in key.split():
            candidate = find_candidate(token)
            if candidate:
                break
    if candidate:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(candidate, dest_path)
        print(f'Copied {candidate} -> {dest_path}')
        copied += 1
    else:
        not_found.append((p.id, p.name, basename))

print(f'Finished. Copied: {copied}. Not found: {len(not_found)}')
if not_found:
    print('\nMissing for:')
    for t in not_found:
        print(t)
