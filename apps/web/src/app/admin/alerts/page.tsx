'use client';

import { useState, useEffect } from 'react';
import {
    Bell,
    RefreshCw,
    Check,
    X,
    AlertCircle,
    AlertTriangle,
    Info,
    CheckCircle
} from 'lucide-react';

interface Alert {
    id: string;
    type: 'error' | 'warning' | 'info';
    source: string;
    message: string;
    meta: Record<string, unknown>;
    is_read: boolean;
    created_at: string;
}

interface AlertStats {
    total: number;
    unread: number;
    by_type: Record<string, number>;
}

const TYPE_CONFIG = {
    error: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-l-red-500' },
    warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-l-yellow-500' },
    info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-l-blue-500' },
};

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [stats, setStats] = useState<AlertStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchAlerts();
    }, [filter]);

    const fetchAlerts = async () => {
        try {
            setLoading(true);
            let url = `${ENGINE_URL}/api/v1/alerts?limit=100`;
            if (filter === 'unread') {
                url += '&is_read=false';
            } else if (filter !== 'all') {
                url += `&type=${filter}`;
            }

            const [alertsRes, statsRes] = await Promise.all([
                fetch(url),
                fetch(`${ENGINE_URL}/api/v1/alerts/stats`),
            ]);

            if (alertsRes.ok) {
                const data = await alertsRes.json();
                setAlerts(data.alerts || []);
            }

            if (statsRes.ok) {
                const data = await statsRes.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: string) => {
        try {
            await fetch(`${ENGINE_URL}/api/v1/alerts/${id}/read`, { method: 'POST' });
            setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
            if (stats) {
                setStats({ ...stats, unread: Math.max(0, stats.unread - 1) });
            }
        } catch (err) {
            console.error('Failed to mark alert as read:', err);
        }
    };

    const markAllAsRead = async () => {
        try {
            await fetch(`${ENGINE_URL}/api/v1/alerts/read-all`, { method: 'POST' });
            setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
            if (stats) {
                setStats({ ...stats, unread: 0 });
            }
        } catch (err) {
            console.error('Failed to mark all as read:', err);
        }
    };

    const deleteAlert = async (id: string) => {
        try {
            await fetch(`${ENGINE_URL}/api/v1/alerts/${id}`, { method: 'DELETE' });
            setAlerts(prev => prev.filter(a => a.id !== id));
        } catch (err) {
            console.error('Failed to delete alert:', err);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                            <Bell className="w-6 h-6 text-blue-400" />
                            알림
                        </h1>
                        {stats && (
                            <p className="text-slate-400 text-sm mt-1">
                                {stats.unread > 0 ? `${stats.unread}개의 읽지 않은 알림` : '모든 알림을 읽었습니다'}
                            </p>
                        )}
                    </div>
                    <div className="flex gap-3">
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">전체</option>
                            <option value="unread">읽지 않음</option>
                            <option value="error">오류</option>
                            <option value="warning">경고</option>
                            <option value="info">정보</option>
                        </select>
                        <button
                            onClick={markAllAsRead}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <CheckCircle className="w-4 h-4" />
                            모두 읽음
                        </button>
                        <button
                            onClick={fetchAlerts}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="text-sm text-slate-400 mb-1">전체</div>
                            <div className="text-3xl font-bold text-white">{stats.total}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-2 mb-1">
                                <AlertCircle className="w-4 h-4 text-red-400" />
                                <span className="text-sm text-red-400">오류</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_type.error || 0}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-2 mb-1">
                                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                                <span className="text-sm text-yellow-400">경고</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_type.warning || 0}</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                            <div className="flex items-center gap-2 mb-1">
                                <Info className="w-4 h-4 text-blue-400" />
                                <span className="text-sm text-blue-400">정보</span>
                            </div>
                            <div className="text-3xl font-bold text-white">{stats.by_type.info || 0}</div>
                        </div>
                    </div>
                )}

                {/* Alerts List */}
                <div className="space-y-3">
                    {loading ? (
                        <div className="text-center py-8 text-slate-400">로딩 중...</div>
                    ) : alerts.length === 0 ? (
                        <div className="text-center py-12 bg-slate-900 border border-slate-800 rounded-xl">
                            <div className="text-4xl mb-2">🎉</div>
                            <div className="text-slate-400">알림이 없습니다</div>
                        </div>
                    ) : (
                        alerts.map((alert) => {
                            const config = TYPE_CONFIG[alert.type];
                            const IconComponent = config.icon;

                            return (
                                <div
                                    key={alert.id}
                                    className={`p-4 rounded-xl border-l-4 ${config.border} ${config.bg} ${alert.is_read ? 'opacity-60' : ''
                                        }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <IconComponent className={`w-4 h-4 ${config.color}`} />
                                                <span className="font-medium text-white">{alert.source}</span>
                                                <span className="text-xs text-slate-400">
                                                    {formatDate(alert.created_at)}
                                                </span>
                                                {!alert.is_read && (
                                                    <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                                                        NEW
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-slate-300">{alert.message}</p>
                                        </div>
                                        <div className="flex gap-2 ml-4">
                                            {!alert.is_read && (
                                                <button
                                                    onClick={() => markAsRead(alert.id)}
                                                    className="p-1.5 text-slate-400 hover:text-green-400 transition-colors"
                                                >
                                                    <Check className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => deleteAlert(alert.id)}
                                                className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
}
