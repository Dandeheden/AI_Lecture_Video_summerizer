import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  HelpCircle,
  Clock,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Send,
  Sparkles
} from 'lucide-react';
import api from '../services/api';

export default function QuizPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quiz taking state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({}); // { question_id: selected_option_text }
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Generator settings
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState('Medium');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    loadQuiz();
  }, [id]);

  // Quiz Timer
  useEffect(() => {
    if (!quizData || !quizData.questions || quizData.questions.length === 0) return;
    const interval = setInterval(() => {
      setTimerSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [quizData]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getLatestQuiz(id);
      setQuizData(res);
      setUserAnswers({});
      setCurrentIndex(0);
      setTimerSeconds(0);
    } catch (err) {
      // If 404, we let student generate a new quiz
      if (err.response?.status === 404) {
        setQuizData(null);
      } else {
        setError(err.response?.data?.detail || 'Failed to load quiz for this lecture.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuiz = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const res = await api.generateQuiz(id, {
        question_count: questionCount,
        difficulty_level: difficulty,
      });
      setQuizData(res);
      setUserAnswers({});
      setCurrentIndex(0);
      setTimerSeconds(0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz questions.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectOption = (optionText) => {
    const currentQ = quizData.questions[currentIndex];
    setUserAnswers((prev) => ({
      ...prev,
      [currentQ.id]: optionText,
    }));
  };

  const clearSelection = () => {
    const currentQ = quizData.questions[currentIndex];
    setUserAnswers((prev) => {
      const copy = { ...prev };
      delete copy[currentQ.id];
      return copy;
    });
  };

  const handleSubmitQuiz = async () => {
    setIsSubmitting(true);
    setShowConfirmModal(false);

    const submissionPayload = {
      answers: Object.entries(userAnswers).map(([qid, ans]) => ({
        question_id: parseInt(qid),
        selected_option: ans,
      })),
      time_taken_seconds: timerSeconds,
    };

    try {
      const result = await api.submitQuiz(quizData.quiz_id, submissionPayload);
      navigate(`/lectures/${id}/quiz/results/${result.attempt_id}`);
    } catch (err) {
      setIsSubmitting(false);
      setError(err.response?.data?.detail || 'Failed to submit quiz. Please try again.');
    }
  };

  const formatTimer = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        <p className="text-slate-400 text-sm">Loading lecture quiz...</p>
      </div>
    );
  }

  // Quiz Generator UI if no quiz exists yet
  if (!quizData || !quizData.questions || quizData.questions.length === 0) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16">
        <Link
          to={`/lectures/${id}/summary`}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-6"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Summary</span>
        </Link>

        <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center">
          <div className="w-12 h-12 rounded-2xl bg-purple-950 border border-purple-800 flex items-center justify-center text-purple-400 mx-auto mb-4">
            <Sparkles className="w-6 h-6" />
          </div>

          <h2 className="text-xl font-bold text-white mb-2">Generate Practice Quiz</h2>
          <p className="text-xs text-slate-400 mb-6">
            Create an interactive practice quiz automatically extracted from the key propositions of this lecture.
          </p>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div className="space-y-4 text-left mb-6">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Number of Questions
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[5, 10, 15].map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setQuestionCount(count)}
                    className={`py-2 rounded-xl text-xs font-semibold border transition-colors ${
                      questionCount === count
                        ? 'bg-purple-600 text-white border-purple-500'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    {count} Questions
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['Easy', 'Medium', 'Hard'].map((diff) => (
                  <button
                    key={diff}
                    type="button"
                    onClick={() => setDifficulty(diff)}
                    className={`py-2 rounded-xl text-xs font-semibold border transition-colors ${
                      difficulty === diff
                        ? 'bg-indigo-600 text-white border-indigo-500'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerateQuiz}
            disabled={isGenerating}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold text-sm shadow-lg shadow-purple-500/25 hover:from-purple-500 hover:to-indigo-500 transition-all flex items-center justify-center space-x-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Synthesizing MCQs...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Questions Now</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  const currentQ = quizData.questions[currentIndex];
  const totalQuestions = quizData.questions.length;
  const answeredCount = Object.keys(userAnswers).length;
  const progressPercent = Math.round(((currentIndex + 1) / totalQuestions) * 100);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-6">
        <Link
          to={`/lectures/${id}/summary`}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Exit to Summary</span>
        </Link>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono">
            <Clock className="w-3.5 h-3.5 text-purple-400" />
            <span>{formatTimer(timerSeconds)}</span>
          </div>

          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-950/80 border border-indigo-800 text-indigo-300">
            {quizData.difficulty_level}
          </span>
        </div>
      </div>

      {/* Progress & Question Tracker */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 mb-6">
        <div className="flex items-center justify-between text-xs text-slate-300 mb-2">
          <span>Question {currentIndex + 1} of {totalQuestions}</span>
          <span>{answeredCount} of {totalQuestions} Answered</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-3">
          <div
            className="bg-purple-600 h-full rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Question Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
          {quizData.questions.map((q, idx) => {
            const isAnswered = Boolean(userAnswers[q.id]);
            const isCurrent = idx === currentIndex;
            return (
              <button
                key={q.id}
                onClick={() => setCurrentIndex(idx)}
                className={`w-7 h-7 rounded-lg text-xs font-bold transition-all flex items-center justify-center flex-shrink-0 ${
                  isCurrent
                    ? 'ring-2 ring-purple-500 bg-purple-600 text-white'
                    : isAnswered
                    ? 'bg-purple-950 border border-purple-700 text-purple-300'
                    : 'bg-slate-900 border border-slate-800 text-slate-500 hover:text-slate-300'
                }`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Question Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 mb-6">
        <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">
          Question {currentIndex + 1}
        </div>
        <h2 className="text-lg sm:text-xl font-bold text-white mb-6 leading-relaxed">
          {currentQ.question}
        </h2>

        {/* 4 Answer Options */}
        <div className="space-y-3">
          {currentQ.options.map((optionText, optIdx) => {
            const optLetter = String.fromCharCode(65 + optIdx); // A, B, C, D
            const isSelected = userAnswers[currentQ.id] === optionText;

            return (
              <div
                key={optIdx}
                onClick={() => handleSelectOption(optionText)}
                className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start space-x-3 ${
                  isSelected
                    ? 'bg-purple-950/40 border-purple-500 text-white ring-1 ring-purple-500/50 shadow-md shadow-purple-950/50'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${
                    isSelected
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {optLetter}
                </div>
                <div className="text-sm font-medium leading-relaxed flex-1">
                  {optionText}
                </div>
                {isSelected && (
                  <CheckCircle2 className="w-5 h-5 text-purple-400 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          disabled={currentIndex === 0}
          className={`px-4 py-2.5 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
            currentIndex === 0
              ? 'border-slate-800 text-slate-600 cursor-not-allowed'
              : 'border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800'
          }`}
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Previous</span>
        </button>

        {userAnswers[currentQ.id] && (
          <button
            onClick={clearSelection}
            className="text-xs text-slate-400 hover:text-slate-200 underline font-medium"
          >
            Clear selection
          </button>
        )}

        {currentIndex < totalQuestions - 1 ? (
          <button
            onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors"
          >
            <span>Next Question</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={() => setShowConfirmModal(true)}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.02]"
          >
            <Send className="w-4 h-4" />
            <span>Submit Quiz</span>
          </button>
        )}
      </div>

      {/* Submit Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-700 max-w-md w-full text-center">
            <h3 className="text-lg font-bold text-white mb-2">Ready to Submit Quiz?</h3>
            <p className="text-xs text-slate-400 mb-6">
              You answered <span className="font-bold text-purple-400">{answeredCount}</span> of{' '}
              <span className="font-bold text-white">{totalQuestions}</span> questions.
              {answeredCount < totalQuestions && (
                <span className="block mt-2 text-amber-400">
                  Warning: {totalQuestions - answeredCount} unanswered questions will be marked incorrect.
                </span>
              )}
            </p>

            <div className="flex items-center justify-center space-x-3">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Review Answers
              </button>

              <button
                onClick={handleSubmitQuiz}
                disabled={isSubmitting}
                className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Grading...</span>
                  </>
                ) : (
                  <span>Confirm & Grade</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
