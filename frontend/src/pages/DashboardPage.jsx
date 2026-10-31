import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Video,
  Clock,
  HelpCircle,
  Award,
  Upload,
  ArrowRight,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw
} from 'lucide-react';
import api from '../services/api';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      setError(null);
      const [statsData, historyData] = await Promise.all([
        api.getDashboardStats().catch(() => ({
          total_lectures: 0,
          completed_lectures: 0,
          total_minutes_processed: 0,
          total_quizzes_taken: 0,
          average_quiz_score: 0,
          recent_attempts: []
        })),
        api.getHistory().catch(() => ({ total_lectures: 0, lectures: [] }))
      ]);
      setStats(statsData);
      setHistory(historyData.lectures || []);
    } catch (err) {
      setError('Could not connect to backend server. Make sure FastAPI is running.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 8 seconds if there are processing lectures
    const interval = setInterval(() => {
      loadData();
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="w-3 h-3" />
            <span>Ready</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-400 border border-rose-800/60">
            <AlertCircle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span className="capitalize">{status}...</span>
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        <p className="text-slate-400 text-sm">Loading lecture analytics...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Learning Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time analytics and fast access to your processed lectures and quizzes.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 text-sm font-medium transition-colors"
            title="Refresh statistics"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-purple-400' : ''}`} />
          </button>

          <Link
            to="/upload"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-sm shadow-lg shadow-purple-500/20 transition-all hover:scale-[1.02]"
          >
            <Upload className="w-4 h-4" />
            <span>Upload New Lecture</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => loadData(true)} className="underline hover:text-white font-medium">Retry</button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 glow-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Lectures</span>
            <div className="w-10 h-10 rounded-xl bg-purple-950/60 border border-purple-800/50 flex items-center justify-center text-purple-400">
              <Video className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white mt-4">{stats?.total_lectures || 0}</div>
          <p className="text-xs text-slate-400 mt-1">
            {stats?.completed_lectures || 0} completed processing
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 glow-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Minutes Processed</span>
            <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-800/50 flex items-center justify-center text-indigo-400">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white mt-4">{stats?.total_minutes_processed || 0} m</div>
          <p className="text-xs text-slate-400 mt-1">Transcribed with Whisper</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 glow-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Quizzes Attempted</span>
            <div className="w-10 h-10 rounded-xl bg-sky-950/60 border border-sky-800/50 flex items-center justify-center text-sky-400">
              <HelpCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white mt-4">{stats?.total_quizzes_taken || 0}</div>
          <p className="text-xs text-slate-400 mt-1">Grounded question sessions</p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 glow-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Average Score</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-800/50 flex items-center justify-center text-emerald-400">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white mt-4">
            {stats?.average_quiz_score ? `${stats.average_quiz_score}%` : '—'}
          </div>
          <p className="text-xs text-slate-400 mt-1">Calculated server-side</p>
        </div>
      </div>

      {/* Main Content Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Recent Lectures */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-bold text-white">Recent Lectures</h2>
            <Link to="/history" className="text-xs text-purple-400 hover:text-purple-300 font-medium flex items-center space-x-1">
              <span>View all ({history.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {history.length === 0 ? (
            <div className="glass-panel p-10 rounded-2xl border border-slate-800 text-center">
              <Video className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No lectures uploaded yet</h3>
              <p className="text-xs text-slate-400 mt-1 mb-6">
                Upload your first lecture video or audio file to get started.
              </p>
              <Link
                to="/upload"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>Upload Lecture</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {history.slice(0, 5).map((lec) => (
                <div
                  key={lec.id}
                  className="glass-panel p-5 rounded-2xl border border-slate-800 glow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="flex items-start space-x-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-purple-400 flex-shrink-0 mt-0.5">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <h4 className="text-sm font-bold text-white truncate max-w-xs">{lec.title}</h4>
                        {getStatusBadge(lec.status)}
                      </div>
                      <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                        <span>{lec.file_type.toUpperCase()}</span>
                        <span>•</span>
                        <span>{lec.duration_seconds > 0 ? `${Math.round(lec.duration_seconds / 60)} mins` : `${lec.file_size_mb} MB`}</span>
                        <span>•</span>
                        <span>{new Date(lec.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 sm:self-center self-end">
                    {lec.status === 'completed' ? (
                      <>
                        <Link
                          to={`/lectures/${lec.id}/summary`}
                          className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-medium transition-colors"
                        >
                          Notes & Summary
                        </Link>
                        <Link
                          to={`/lectures/${lec.id}/quiz`}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-colors"
                        >
                          Quiz
                        </Link>
                      </>
                    ) : (
                      <Link
                        to={`/upload?monitor=${lec.id}`}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                      >
                        Check Progress
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Recent Quiz Attempts */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white">Recent Quiz Attempts</h2>
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
            {(!stats?.recent_attempts || stats.recent_attempts.length === 0) ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                <HelpCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p>No quiz attempts completed yet.</p>
                <p className="mt-1 text-slate-500">Take a quiz on any completed lecture to see results here.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {stats.recent_attempts.map((att) => (
                  <div key={att.attempt_id} className="pt-3 pb-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 pr-2">
                        <h4 className="text-xs font-semibold text-white truncate">{att.lecture_title}</h4>
                        <p className="text-[11px] text-slate-400">
                          {att.correct_answers} of {att.total_questions} correct
                        </p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded ${
                            att.score_percentage >= 70
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-amber-950 text-amber-400 border border-amber-800'
                          }`}
                        >
                          {att.score_percentage}%
                        </span>
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          {new Date(att.completed_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
