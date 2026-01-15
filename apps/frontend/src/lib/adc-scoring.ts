/**
 * ADC Scoring Utility
 * 스코어 기반 ADC 분류 시스템
 */

// ============================================
// Marker Classes
// ============================================

export const ADC_DRUG_SUFFIXES = [
    'vedotin', 'deruxtecan', 'emtansine', 'mafodotin', 'tesirine',
    'ozogamicin', 'govitecan', 'duocarmazine', 'mirvetuximab',
    'loncastuximab', 'ravtansine', 'soravtansine', 'telisotuzumab',
    'tisotumab', 'belantamab', 'enfortumab', 'sacituzumab', 'polatuzumab'
];

export const PAYLOAD_MARKERS = [
    'mmae', 'mmaf', 'dm1', 'dm4', 'dxd', 'sn-38', 'sn38',
    'calicheamicin', 'pbd', 'duocarmycin', 'exatecan',
    'maytansinoid', 'maytansine', 'auristatin', 'topoisomerase',
    'pyrrolobenzodiazepine', 'seco-duocarmycin'
];

export const LINKER_MARKERS = [
    'mc-vc-pabc', 'smcc', 'spdb', 'ggfg', 'vc-pab',
    'valine-citrulline', 'val-cit', 'vc', 'mcc',
    'disulfide', 'hydrazone', 'cleavable linker'
];

export const ADC_KEYWORDS = [
    'adc', 'antibody-drug conjugate', 'antibody drug conjugate',
    'drug conjugate', 'immunoconjugate', 'conjugated antibody'
];

export const COMBINATION_PATTERNS = [
    ' + ', ' plus ', 'combination', 'combined with',
    'in combination', 'followed by', 'with concurrent'
];

// ============================================
// Scoring Function
// ============================================

export interface AdcScoreResult {
    score: number;
    classification: 'adc_confident' | 'adc_possible' | 'not_adc';
    reason: {
        matched_suffixes: string[];
        matched_payloads: string[];
        matched_linkers: string[];
        matched_keywords: string[];
        combination_penalty: boolean;
        combination_ignored: boolean;
    };
}

export function calculateAdcScore(text: string): AdcScoreResult {
    const lowerText = text.toLowerCase();
    let score = 0;

    const matchedSuffixes: string[] = [];
    const matchedPayloads: string[] = [];
    const matchedLinkers: string[] = [];
    const matchedKeywords: string[] = [];

    // Check ADC drug suffixes (+3 each)
    for (const suffix of ADC_DRUG_SUFFIXES) {
        if (lowerText.includes(suffix)) {
            score += 3;
            matchedSuffixes.push(suffix);
        }
    }

    // Check ADC exact phrase (+4)
    if (/antibody[\s-]?drug[\s-]?conjugate/i.test(text)) {
        score += 4;
        matchedKeywords.push('antibody drug conjugate');
    }

    // Check ADC keywords (+2 each)
    for (const keyword of ADC_KEYWORDS) {
        if (keyword !== 'antibody-drug conjugate' &&
            keyword !== 'antibody drug conjugate' &&
            lowerText.includes(keyword)) {
            score += 2;
            matchedKeywords.push(keyword);
        }
    }

    // Check Payload markers (+2 each)
    for (const payload of PAYLOAD_MARKERS) {
        if (lowerText.includes(payload)) {
            score += 2;
            matchedPayloads.push(payload);
        }
    }

    // Check Linker markers (+1 each)
    for (const linker of LINKER_MARKERS) {
        if (lowerText.includes(linker)) {
            score += 1;
            matchedLinkers.push(linker);
        }
    }

    // Check combination penalty (-3, but ignored if suffix found)
    let combinationPenalty = false;
    let combinationIgnored = false;

    for (const pattern of COMBINATION_PATTERNS) {
        if (lowerText.includes(pattern)) {
            combinationPenalty = true;
            break;
        }
    }

    if (combinationPenalty) {
        if (matchedSuffixes.length > 0) {
            // Has ADC suffix, ignore combination penalty
            combinationIgnored = true;
        } else {
            score -= 3;
        }
    }

    // Classification
    let classification: 'adc_confident' | 'adc_possible' | 'not_adc';

    if (score >= 5 || matchedSuffixes.length > 0) {
        classification = 'adc_confident';
    } else if (score >= 3) {
        classification = 'adc_possible';
    } else {
        classification = 'not_adc';
    }

    return {
        score,
        classification,
        reason: {
            matched_suffixes: matchedSuffixes,
            matched_payloads: matchedPayloads,
            matched_linkers: matchedLinkers,
            matched_keywords: matchedKeywords,
            combination_penalty: combinationPenalty,
            combination_ignored: combinationIgnored
        }
    };
}

// ============================================
// Gate Validation
// ============================================

export interface GateCheckResult {
    passed: boolean;
    missingRequirements: string[];
}

export function checkPromotionGate(seed: {
    resolved_target_symbol?: string | null;
    payload_smiles_standardized?: string | null;
    proxy_smiles_flag?: boolean;
    adc_classification?: string;
    is_adc_confirmed?: boolean;
    evidence_refs?: any[];
}): GateCheckResult {
    const missing: string[] = [];

    // 1. Target required
    if (!seed.resolved_target_symbol) {
        missing.push('resolved_target_symbol');
    }

    // 2. SMILES or Proxy required
    if (!seed.payload_smiles_standardized && !seed.proxy_smiles_flag) {
        missing.push('payload_smiles (or proxy)');
    }

    // 3. ADC classification
    if (!['adc_confident', 'adc_possible'].includes(seed.adc_classification || '')) {
        missing.push('adc_classification (must be confident or possible)');
    }

    // 4. ADC confirmed by admin
    if (!seed.is_adc_confirmed) {
        missing.push('is_adc_confirmed');
    }

    // 5. Evidence
    if (!seed.evidence_refs || seed.evidence_refs.length === 0) {
        missing.push('evidence_refs (at least 1)');
    }

    return {
        passed: missing.length === 0,
        missingRequirements: missing
    };
}
