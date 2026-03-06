import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../api/api";
import ChatModal from "../components/ChatModal";

export default function ResumeChat() {
  const { documentId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [readyDocId, setReadyDocId] = useState(null);
  const [loading, setLoading] = useState(true);

  const paper = {
    title: location.state?.title || "Previous Session"
  };

  useEffect(() => {
    const ensureReady = async () => {
      try {
        const res = await api.get(`/chat/${documentId}`);
        if (res.data?.messages) {
          setReadyDocId(documentId);
        }
      } catch {
        console.error("Resume chat failed");
      } finally {
        setLoading(false);
      }
    };

    ensureReady();
  }, [documentId]);

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading chat...</div>;
  }

  if (!readyDocId) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Failed to load chat session.</div>;
  }

  return (
    <ChatModal
      documentId={readyDocId}
      paper={paper}
      onClose={() => navigate("/dashboard")}
    />
  );
}