import { useState, useEffect, useRef, useCallback } from 'react';

// SpeechRecognition type declarations for browsers
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

export function useSpeechRecognition() {
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [voiceLatencyMs, setVoiceLatencyMs] = useState<number | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const recognitionRef = useRef<any>(null);
  const speechStartTimeRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
        speechStartTimeRef.current = performance.now();
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          if (res.isFinal) {
            currentFinal += res[0].transcript;
          } else {
            currentInterim += res[0].transcript;
          }
        }

        if (currentFinal) {
          setTranscript((prev) => (prev ? `${prev} ${currentFinal.trim()}` : currentFinal.trim()));
          if (speechStartTimeRef.current) {
            const duration = Math.round(performance.now() - speechStartTimeRef.current);
            setVoiceLatencyMs(duration);
          }
        }
        setInterimTranscript(currentInterim);
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          setError('Microphone access denied. Please allow microphone permissions in your browser.');
        } else if (event.error === 'no-speech') {
          setError('No speech was detected. Please try speaking again.');
        } else {
          setError(`Speech recognition notice: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        stopAudioAnalyser();
      };

      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      setError('Native speech recognition is not supported in this browser. Please use text input.');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      stopAudioAnalyser();
    };
  }, []);

  const startAudioAnalyser = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
        animationFrameRef.current = requestAnimationFrame(updateLevel);
      };

      updateLevel();
    } catch (err) {
      console.warn('Could not initialize microphone audio analyser:', err);
    }
  };

  const stopAudioAnalyser = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);
  };

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      setError('Speech recognition not available.');
      return;
    }
    setError(null);
    setTranscript('');
    setInterimTranscript('');
    setVoiceLatencyMs(null);
    try {
      recognitionRef.current.start();
      startAudioAnalyser();
    } catch (err) {
      console.warn('Speech recognition start failed or already active:', err);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // ignore
      }
    }
    setIsListening(false);
    stopAudioAnalyser();
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setVoiceLatencyMs(null);
    setError(null);
  }, []);

  return {
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    error,
    voiceLatencyMs,
    audioLevel,
    startListening,
    stopListening,
    resetTranscript,
    setTranscript,
  };
}
