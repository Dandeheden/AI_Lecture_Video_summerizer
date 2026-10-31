import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Health
  getHealth: () => client.get('/health').then((r) => r.data),

  // Lecture Operations
  uploadLecture: (formData, onUploadProgress) =>
    client.post('/lectures/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }).then((r) => r.data),

  getLectureStatus: (id) => client.get(`/lectures/${id}/status`).then((r) => r.data),
  getLectureTranscript: (id) => client.get(`/lectures/${id}/transcript`).then((r) => r.data),
  getLectureSummary: (id) => client.get(`/lectures/${id}/summary`).then((r) => r.data),
  getLectureNotes: (id) => client.get(`/lectures/${id}/notes`).then((r) => r.data),
  deleteLecture: (id) => client.delete(`/lectures/${id}`).then((r) => r.data),

  // Quiz Operations
  generateQuiz: (lectureId, payload) =>
    client.post(`/lectures/${lectureId}/quiz`, payload).then((r) => r.data),

  getLatestQuiz: (lectureId) =>
    client.get(`/lectures/${lectureId}/quiz`).then((r) => r.data),

  submitQuiz: (quizId, payload) =>
    client.post(`/quizzes/${quizId}/submit`, payload).then((r) => r.data),

  getQuizAttempt: (quizId, attemptId) =>
    client.get(`/quizzes/${quizId}/attempts/${attemptId}`).then((r) => r.data),

  // History and Statistics
  getHistory: () => client.get('/history').then((r) => r.data),
  getDashboardStats: () => client.get('/history/stats').then((r) => r.data),
};

export default api;
