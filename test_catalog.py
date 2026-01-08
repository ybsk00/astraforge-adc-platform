import requests

# Check catalog items
r = requests.get('http://localhost:8000/api/v1/catalog?limit=25')
data = r.json()
items = data.get('items', [])
print(f'Total items in catalog: {len(items)}')
print('---')

# Group by type
types = {}
for item in items:
    t = item.get('type', 'unknown')
    if t not in types:
        types[t] = []
    types[t].append(item)

for t, items_list in types.items():
    print(f'\n{t.upper()} ({len(items_list)}):')
    for item in items_list[:5]:
        ext_ids = []
        if item.get('uniprot_accession'):
            ext_ids.append(f"UniProt:{item['uniprot_accession']}")
        if item.get('pubchem_cid'):
            ext_ids.append(f"PubChem:{item['pubchem_cid']}")
        if item.get('chembl_id'):
            ext_ids.append(f"ChEMBL:{item['chembl_id']}")
        id_str = ', '.join(ext_ids) if ext_ids else 'No external IDs'
        print(f"  - {item['name']}: {id_str}")
