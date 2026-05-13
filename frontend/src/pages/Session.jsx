import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getSession, uploadPDF, uploadYoutube, uploadWebpage, getUploadProgress } from "../api/api";
import Navbar from "../components/Navbar";
import LoadingSpinner from "../components/LoadingSpinner";
import styles from "./Session.module.css";

const TABS = ["PDF", "YouTube", "Webpage"];

export default function Session() {
  const { id } = useParams();
  const nav = useNavigate();
  
  const [session, setSession] = useState(null);
  const [tab, setTab] = useState("PDF");
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(null);
  const [progressInterval, setProgressInterval] = useState(null);
  const [startTime, setStartTime] = useState(null);

  const load = async () => {
    try {
      const { data } = await getSession(id);
      setSession(data);
      // ✅ Auto-redirect to practice if questions exist
      if (data.question_count > 0 && loading) {
        setLoading(false);
        setProgress(null);
        if (progressInterval) clearInterval(progressInterval);
      }
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  };

  useEffect(() => {
    load();
    return () => {
      if (progressInterval) clearInterval(progressInterval);
    };
  }, [id]);

  const startProgressPolling = () => {
    setStartTime(Date.now());
    fetchProgress();
    const interval = setInterval(fetchProgress, 1000);
    setProgressInterval(interval);
  };

  const stopProgressPolling = () => {
    if (progressInterval) {
      clearInterval(progressInterval);
      setProgressInterval(null);
    }
  };

  const fetchProgress = async () => {
    try {
      const { data } = await getUploadProgress(id);
      setProgress(data);
      
      // ✅ Stop polling when complete, error, idle, or after 10 minutes
      const elapsed = Date.now() - startTime;
      if (
        data.status === "complete" || 
        data.status === "error" || 
        data.status === "idle" ||
        elapsed > 10 * 60 * 1000
      ) {
        stopProgressPolling();
        setLoading(false);
        setProgress(null);
        await load(); // Refresh session data
        if (data.status === "complete") {
          notify("success", "Questions generated successfully!");
          // ✅ Auto-redirect to practice after 2 seconds
          setTimeout(() => {
            nav(`/session/${id}/practice`);
          }, 2000);
        } else if (data.status === "error") {
          notify("error", data.message || "Processing failed");
        }
      }
    } catch (err) {
      console.error("Failed to fetch progress:", err);
      stopProgressPolling();
      setLoading(false);
    }
  };

  const notify = (type, text) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 4000);
  };

  const handleUpload = async () => {
    setLoading(true);
    setProgress(null);
    startProgressPolling();
    
    try {
      if (tab === "PDF") {
        if (!file) return notify("error", "Select a PDF.");
        if (file.size > 5 * 1024 * 1024) {
          return notify("error", "PDF must be under 5MB.");
        }
        await uploadPDF(id, file);
        setFile(null);
      } else if (tab === "YouTube") {
        if (!url.trim()) return notify("error", "Enter YouTube URL.");
        await uploadYoutube(id, url.trim());
        setUrl("");
      } else {
        if (!url.trim()) return notify("error", "Enter webpage URL.");
        await uploadWebpage(id, url.trim());
        setUrl("");
      }
    } catch (e) {
      console.error("Upload error:", e);
      stopProgressPolling();
      setLoading(false);
      notify("error", e.response?.data?.error || "Something went wrong.");
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") {
      setFile(f);
    } else {
      notify("error", "PDF only.");
    }
  };

  const getProgressPercent = () => {
    if (!progress || !progress.total_chunks) return 0;
    return Math.min(100, Math.round((progress.current_chunk / progress.total_chunks) * 100));
  };

  const getStatusIcon = () => {
    if (!progress) return "⏳";
    switch(progress.status) {
      case "extracting": return "📄";
      case "vectorizing": return "📊";
      case "generating": return "🤖";
      case "summarizing": return "📝";
      case "saving": return "💾";
      case "complete": return "✅";
      case "error": return "❌";
      default: return "⏳";
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (!session) {
    return (
      <div className={styles.page}>
        <Navbar />
        <div className={styles.loadingContainer}>
          <p>Loading session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Navbar />
      
      {loading && progress && (
        <div className={styles.progressOverlay}>
          <div className={styles.progressCard}>
            <div className={styles.progressIcon}>{getStatusIcon()}</div>
            <h3 className={styles.progressTitle}>
              {progress.status === "extracting" && "📄 Extracting Content..."}
              {progress.status === "vectorizing" && "📊 Processing Text..."}
              {progress.status === "generating" && "🤖 Generating Questions with AI..."}
              {progress.status === "summarizing" && "📝 Creating Summary..."}
              {progress.status === "saving" && "💾 Saving to Database..."}
              {progress.status === "complete" && "✅ Complete! Redirecting to Practice..."}
              {progress.status === "error" && "❌ Error Occurred"}
            </h3>
            <p className={styles.progressMessage}>{progress.message}</p>
            
            {progress.total_chunks > 0 && (
              <>
                <div className={styles.progressBarContainer}>
                  <div 
                    className={styles.progressBarFill}
                    style={{ width: `${getProgressPercent()}%` }}
                  />
                </div>
                <p className={styles.progressPercent}>
                  {getProgressPercent()}% complete
                </p>
              </>
            )}
            
            <div className={styles.progressStats}>
              {progress.total_chunks > 0 && (
                <div className={styles.stat}>
                  <span className={styles.statLabel}>Chunks:</span>
                  <span className={styles.statValue}>{progress.current_chunk}/{progress.total_chunks}</span>
                </div>
              )}
              {progress.questions_generated > 0 && (
                <div className={styles.stat}>
                  <span className={styles.statLabel}>Questions:</span>
                  <span className={styles.statValue}>{progress.questions_generated}</span>
                </div>
              )}
              {startTime && (
                <div className={styles.stat}>
                  <span className={styles.statLabel}>Time:</span>
                  <span className={styles.statValue}>{formatTime(Math.floor((Date.now() - startTime) / 1000))}</span>
                </div>
              )}
            </div>
            
            <p className={styles.progressHint}>
              {progress.total_chunks > 10 
                ? "Large file detected. This may take 2-5 minutes."
                : "This may take 1-2 minutes. Please wait..."}
            </p>
            
            <button 
              className={styles.cancelBtn}
              onClick={() => {
                stopProgressPolling();
                setLoading(false);
                setProgress(null);
                notify("info", "Processing cancelled");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      <div className={styles.container}>
        <div className={styles.header}>
          <button className={styles.back} onClick={() => nav("/")}>← Back</button>
          <div>
            <h1 className={styles.title}>{session.title}</h1>
            <p className={styles.meta}>
              {session.source_count ?? 0} sources · {session.question_count ?? 0} questions
            </p>
          </div>
          
          {session.question_count > 0 && (
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button 
                className={styles.practiceBtn} 
                onClick={() => nav(`/session/${id}/practice`)}
              >
                Start Practice →
              </button>
              <button 
                className={styles.allQaBtn}
                onClick={() => nav(`/session/${id}/all-qa`)}
              >
                📋 View All Q&A
              </button>
            </div>
          )}
        </div>

        {msg && (
          <div className={`${styles.toast} ${styles[msg.type]}`}>
            {msg.text}
          </div>
        )}

        <div className={styles.uploadCard}>
          <h2 className={styles.cardTitle}>Add Study Material</h2>
          <p className={styles.cardSub}>
            Upload a source and AI will generate interview-style questions.
          </p>

          <div className={styles.tabs}>
            {TABS.map((t) => (
              <button
                key={t}
                className={`${styles.tab} ${tab === t ? styles.activeTab : ""}`}
                onClick={() => {
                  setTab(t);
                  setUrl("");
                  setFile(null);
                }}
              >
                {t === "PDF" ? "📄 PDF" : t === "YouTube" ? "▶️ YouTube" : "🌐 Webpage"}
              </button>
            ))}
          </div>

          {tab === "PDF" ? (
            <div
              className={`${styles.dropzone} ${dragging ? styles.dragging : ""}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => document.getElementById("fileInput").click()}
            >
              <input
                id="fileInput"
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              
              {file ? (
                <div className={styles.fileSelected}>
                  <span>📄</span>
                  <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {file.name}
                  </span>
                  <span style={{ fontSize: "12px", color: "var(--muted)" }}>
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                  <button 
                    className={styles.clearFile} 
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <>
                  <div className={styles.dropIcon}>📁</div>
                  <p className={styles.dropText}>
                    Drag & drop PDF or <span className={styles.browse}>browse</span>
                  </p>
                  <p className={styles.dropHint}>
                    Notes, textbooks, any study material (under 5MB)
                  </p>
                </>
              )}
            </div>
          ) : (
            <div className={styles.urlInput}>
              <input
                placeholder={
                  tab === "YouTube"
                    ? "https://www.youtube.com/watch?v=..."
                    : "https://example.com/article"
                }
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          )}

          <button 
            className={styles.uploadBtn} 
            onClick={handleUpload} 
            disabled={loading || (tab === "PDF" && !file) || (tab !== "PDF" && !url.trim())}
          >
            {loading ? "⏳ Processing... please wait" : "⚡ Generate Questions"}
          </button>
        </div>

        {session.sources?.length > 0 && (
          <div className={styles.sourcesList}>
            <h3 className={styles.sourcesTitle}>Added Sources</h3>
            {session.sources.map((s) => (
              <div key={s.id} className={styles.sourceItem}>
                <span>
                  {s.type === "pdf" ? "📄" : s.type === "youtube" ? "▶️" : "🌐"}
                </span>
                <span className={styles.sourceName}>{s.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}