/**
 * 화학 구조 Resolver 유틸리티 (v2)
 * PubChem PUG REST 및 OPSIN API 연동
 */

const PUBCHEM_BASE_URL = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug';
const OPSIN_BASE_URL = 'https://opsin.ch.cam.ac.uk/opsin';

export interface ResolvedCandidate {
    name: string;
    smiles: string;
    inchi_key: string;
    external_id: string;
    source: 'pubchem' | 'opsin';
    confidence: number;
}

/**
 * PubChem을 통한 구조 조회
 */
async function resolveFromPubChem(name: string): Promise<ResolvedCandidate[]> {
    try {
        // 1. Name으로 CID 조회
        const cidRes = await fetch(`${PUBCHEM_BASE_URL}/compound/name/${encodeURIComponent(name)}/cids/JSON`);
        if (!cidRes.ok) return [];
        const cidData = await cidRes.json();
        const cids = cidData.IdentifierList?.CID || [];

        if (cids.length === 0) return [];

        // 2. CID로 상세 정보(SMILES, InChIKey) 조회 (최대 5개 후보)
        const targetCids = cids.slice(0, 5).join(',');
        const propRes = await fetch(`${PUBCHEM_BASE_URL}/compound/cid/${targetCids}/property/CanonicalSMILES,IsomericSMILES,InChIKey/JSON`);
        if (!propRes.ok) return [];
        const propData = await propRes.json();
        const properties = propData.PropertyTable?.Properties || [];

        return properties.map((p: any) => {
            let confidence = 40; // Exact name match 기본 점수
            if (cids.length === 1) confidence += 30; // 단일 후보 보너스
            if (p.InChIKey) confidence += 20; // InChIKey 존재 보너스

            return {
                name: name,
                smiles: p.IsomericSMILES || p.CanonicalSMILES,
                inchi_key: p.InChIKey,
                external_id: p.CID.toString(),
                source: 'pubchem',
                confidence: Math.min(confidence, 100)
            };
        });
    } catch (error) {
        console.error('PubChem resolve error:', error);
        return [];
    }
}

/**
 * OPSIN을 통한 구조 조회 (IUPAC명 대응)
 */
async function resolveFromOpsin(name: string): Promise<ResolvedCandidate | null> {
    try {
        const res = await fetch(`${OPSIN_BASE_URL}/${encodeURIComponent(name)}.json`);
        if (!res.ok) return null;
        const data = await res.json();

        if (data.smiles) {
            return {
                name: name,
                smiles: data.smiles,
                inchi_key: data.inchikey,
                external_id: '',
                source: 'opsin',
                confidence: 60 // OPSIN 성공 시 비교적 높은 신뢰도 부여
            };
        }
        return null;
    } catch (error) {
        console.error('OPSIN resolve error:', error);
        return null;
    }
}

/**
 * 통합 구조 Resolver
 */
export async function resolveStructure(name: string, synonyms: string[] = []): Promise<ResolvedCandidate[]> {
    const allNames = [name, ...synonyms].filter(Boolean);
    const results: ResolvedCandidate[] = [];
    const seenInChIKeys = new Set<string>();

    for (const n of allNames) {
        // 1. PubChem 시도
        const pcResults = await resolveFromPubChem(n);
        for (const r of pcResults) {
            if (!seenInChIKeys.has(r.inchi_key)) {
                results.push(r);
                seenInChIKeys.add(r.inchi_key);
            }
        }

        // 2. 결과가 없거나 신뢰도가 낮으면 OPSIN 시도
        if (results.length === 0 || results.every(r => r.confidence < 70)) {
            const opsinResult = await resolveFromOpsin(n);
            if (opsinResult && !seenInChIKeys.has(opsinResult.inchi_key)) {
                results.push(opsinResult);
                seenInChIKeys.add(opsinResult.inchi_key);
            }
        }

        // Throttling 방지 (PubChem 가이드 준수)
        await new Promise(resolve => setTimeout(resolve, 200));
    }

    // 신뢰도 순 정렬
    return results.sort((a, b) => b.confidence - a.confidence);
}
