"use client";

/**
 * 4축 스코어 레이더 차트
 * 
 * Eng-Fit, Bio-Fit, Safety-Fit, Evidence-Fit 시각화
 */
import { useMemo } from "react";

interface ScoreRadarChartProps {
    scores: {
        eng_fit: number;
        bio_fit: number;
        safety_fit: number;
        evidence_fit: number;
    };
    size?: number;
    showLabels?: boolean;
    color?: string;
    compareScores?: {
        eng_fit: number;
        bio_fit: number;
        safety_fit: number;
        evidence_fit: number;
    };
}

const AXIS_LABELS = [
    { key: "eng_fit", label: "Eng", angle: -90 },
    { key: "bio_fit", label: "Bio", angle: 0 },
    { key: "safety_fit", label: "Safety", angle: 90 },
    { key: "evidence_fit", label: "Evidence", angle: 180 },
];

export default function ScoreRadarChart({
    scores,
    size = 200,
    showLabels = true,
    color = "#3B82F6",
    compareScores,
}: ScoreRadarChartProps) {
    const center = size / 2;
    const radius = (size - 40) / 2;

    // Convert score (0-100) to coordinate
    const scoreToPoint = (score: number, axisIndex: number) => {
        const angleRad = ((AXIS_LABELS[axisIndex].angle - 90) * Math.PI) / 180;
        const r = (score / 100) * radius;
        return {
            x: center + r * Math.cos(angleRad),
            y: center + r * Math.sin(angleRad),
        };
    };

    // Generate polygon points for main scores
    const polygonPoints = useMemo(() => {
        return AXIS_LABELS.map((axis, i) => {
            const score = scores[axis.key as keyof typeof scores] || 0;
            return scoreToPoint(score, i);
        });
    }, [scores, center, radius]);

    const polygonPath = polygonPoints.map((p) => `${p.x},${p.y}`).join(" ");

    // Generate comparison polygon if provided
    const comparePolygonPath = useMemo(() => {
        if (!compareScores) return "";
        const points = AXIS_LABELS.map((axis, i) => {
            const score = compareScores[axis.key as keyof typeof compareScores] || 0;
            return scoreToPoint(score, i);
        });
        return points.map((p) => `${p.x},${p.y}`).join(" ");
    }, [compareScores, center, radius]);

    // Grid lines
    const gridLines = [0.25, 0.5, 0.75, 1].map((ratio) => {
        const r = radius * ratio;
        return AXIS_LABELS.map((_, i) => {
            const angleRad = ((AXIS_LABELS[i].angle - 90) * Math.PI) / 180;
            return {
                x: center + r * Math.cos(angleRad),
                y: center + r * Math.sin(angleRad),
            };
        });
    });

    return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            {/* Background */}
            <circle
                cx={center}
                cy={center}
                r={radius}
                fill="rgba(55, 65, 81, 0.3)"
                stroke="rgba(75, 85, 99, 0.5)"
                strokeWidth="1"
            />

            {/* Grid */}
            {gridLines.map((points, i) => (
                <polygon
                    key={i}
                    points={points.map((p) => `${p.x},${p.y}`).join(" ")}
                    fill="none"
                    stroke="rgba(75, 85, 99, 0.3)"
                    strokeWidth="1"
                />
            ))}

            {/* Axis lines */}
            {AXIS_LABELS.map((axis, i) => {
                const angleRad = ((axis.angle - 90) * Math.PI) / 180;
                return (
                    <line
                        key={axis.key}
                        x1={center}
                        y1={center}
                        x2={center + radius * Math.cos(angleRad)}
                        y2={center + radius * Math.sin(angleRad)}
                        stroke="rgba(75, 85, 99, 0.5)"
                        strokeWidth="1"
                    />
                );
            })}

            {/* Compare polygon (if provided) */}
            {compareScores && (
                <polygon
                    points={comparePolygonPath}
                    fill="rgba(239, 68, 68, 0.2)"
                    stroke="#EF4444"
                    strokeWidth="2"
                    strokeDasharray="4,2"
                />
            )}

            {/* Main polygon */}
            <polygon
                points={polygonPath}
                fill={`${color}33`}
                stroke={color}
                strokeWidth="2"
            />

            {/* Points */}
            {polygonPoints.map((point, i) => (
                <circle
                    key={i}
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill={color}
                    stroke="white"
                    strokeWidth="1"
                />
            ))}

            {/* Labels */}
            {showLabels &&
                AXIS_LABELS.map((axis, i) => {
                    const angleRad = ((axis.angle - 90) * Math.PI) / 180;
                    const labelR = radius + 18;
                    const x = center + labelR * Math.cos(angleRad);
                    const y = center + labelR * Math.sin(angleRad);
                    const score = scores[axis.key as keyof typeof scores] || 0;

                    return (
                        <g key={axis.key}>
                            <text
                                x={x}
                                y={y}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                className="text-xs fill-gray-400"
                                fontSize="11"
                            >
                                {axis.label}
                            </text>
                            <text
                                x={x}
                                y={y + 12}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                className="text-xs font-medium"
                                fontSize="10"
                                fill={score >= 70 ? "#4ADE80" : score >= 40 ? "#FACC15" : "#F87171"}
                            >
                                {score.toFixed(0)}
                            </text>
                        </g>
                    );
                })}
        </svg>
    );
}
