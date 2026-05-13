import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
const api = axios.create({ baseURL: BASE });

// Session Management
export const createSession = (title) => api.post("/session/create", { title });
export const listSessions = () => api.get("/sessions");
export const getSession = (id) => api.get("/session/" + id);
export const deleteSession = (id) => api.delete("/session/" + id);

// Upload Sources
export const uploadPDF = (session_id, file) => {
  const fd = new FormData();
  fd.append("session_id", session_id);
  fd.append("file", file);
  return api.post("/upload/pdf", fd);
};

export const uploadYoutube = (session_id, url) => api.post("/upload/youtube", { session_id, url });
export const uploadWebpage = (session_id, url) => api.post("/upload/webpage", { session_id, url });

// Practice & Evaluation
export const getQuestions = (session_id, level) => api.get("/questions/" + session_id, { params: { level } });
export const getAllQuestions = (session_id) => api.get("/questions/all/" + session_id);
export const submitAnswer = (question_id, user_answer) => api.post("/answer", { question_id, user_answer });
export const getProgress = (session_id) => api.get("/progress/" + session_id);

// Progress Tracking (NEW)
export const getUploadProgress = (session_id) => api.get("/progress/" + session_id);