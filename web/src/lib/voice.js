// S8 — voice help on /me. Speech-to-text + a reassuring spoken answer.
// Three tiers, most-capable first, so it always works:
//   1. Deepgram (STT + TTS) when VITE_DEEPGRAM_KEY is set.
//   2. The browser's built-in Web Speech API (no key needed, works in Chrome).
//   3. A typed question (no mic at all) — also how the demo/tests exercise it.
// This is a HELP feature for Margaret, never a control: it can't change protection.
const DEEPGRAM_KEY = import.meta.env.VITE_DEEPGRAM_KEY || "";
const DATA_URL = (import.meta.env.VITE_DATA_URL || "http://localhost:8001").replace(/\/+$/, "");

export const hasDeepgram = !!DEEPGRAM_KEY;
export const speechSupported =
  hasDeepgram ||
  (typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition));

// A calm, reassuring answer. The backend has no Q&A endpoint, so this lives web-side
// and stays deliberately simple and soothing — never alarming, never advice.
export function answerFor(question) {
  const q = (question || "").toLowerCase();
  if (/money|pay|bank|card|account|dollar|bill/.test(q))
    return "Money never leaves your account without your family saying yes first. If someone asks you to pay, I'll check with Priya before anything happens.";
  if (/scam|safe|email|message|fake|fraud|hack|virus/.test(q))
    return "Don't worry. I'm watching your inbox for you. If anything looks risky, I move it aside and check with your family. You never have to decide on your own.";
  if (/lonely|sad|scared|worried|afraid|alone|nervous/.test(q))
    return "You're not alone. Priya is just a phone call away, and I'm here watching out for you. Everything is okay.";
  if (/who are you|what do you do|what are you|help/.test(q))
    return "I'm Lighthouse. I keep an eye on your messages and your money, and I let your family know if anything needs a closer look. You're safe.";
  return "You're protected, and your family is close by. I'm always watching out for you, and I'll let them know if anything important comes up.";
}

// Speak text aloud — Deepgram TTS if available, otherwise the browser's voice.
export async function speak(text) {
  if (hasDeepgram) {
    try {
      const res = await fetch("https://api.deepgram.com/v1/speak?model=aura-asteria-en", {
        method: "POST",
        headers: { Authorization: `Token ${DEEPGRAM_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("deepgram tts " + res.status);
      const audio = new Audio(URL.createObjectURL(await res.blob()));
      await audio.play();
      return;
    } catch {
      /* fall through to the browser voice */
    }
  }
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }
}

// Start listening. Returns a stop() function. Delivers the transcript via onResult.
export function startListening({ onResult, onError, onEnd }) {
  return hasDeepgram
    ? _listenDeepgram({ onResult, onError, onEnd })
    : _listenWebSpeech({ onResult, onError, onEnd });
}

function _listenWebSpeech({ onResult, onError, onEnd }) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    onError && onError("no-speech-recognition");
    return () => {};
  }
  const rec = new SR();
  rec.lang = "en-US";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.onresult = (e) => onResult && onResult(e.results[0][0].transcript);
  rec.onerror = (e) => onError && onError(e.error || "speech-error");
  rec.onend = () => onEnd && onEnd();
  try {
    rec.start();
  } catch {
    onError && onError("start-failed");
  }
  return () => {
    try {
      rec.stop();
    } catch {
      /* noop */
    }
  };
}

function _listenDeepgram({ onResult, onError, onEnd }) {
  let recorder, stream;
  const chunks = [];
  (async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        try {
          const res = await fetch("https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true", {
            method: "POST",
            headers: { Authorization: `Token ${DEEPGRAM_KEY}`, "Content-Type": "audio/webm" },
            body: new Blob(chunks, { type: "audio/webm" }),
          });
          const data = await res.json();
          onResult && onResult(data?.results?.channels?.[0]?.alternatives?.[0]?.transcript || "");
        } catch {
          onError && onError("deepgram-stt");
        } finally {
          stream && stream.getTracks().forEach((t) => t.stop());
          onEnd && onEnd();
        }
      };
      recorder.start();
    } catch {
      onError && onError("mic-denied");
    }
  })();
  return () => {
    try {
      recorder && recorder.state !== "inactive" && recorder.stop();
    } catch {
      /* noop */
    }
  };
}

// Log the question to the family ledger so it appears on the dashboard timeline.
// Fire-and-forget: never blocks or breaks the voice flow if the backend is down.
export function logVoiceQuestion(question) {
  try {
    fetch(`${DATA_URL}/ledger`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: "voice_question",
        details: { title: "Margaret asked a question", detail: question },
        person_id: "11111111-1111-1111-1111-111111111111",
      }),
    }).catch(() => {});
  } catch {
    /* noop */
  }
}
