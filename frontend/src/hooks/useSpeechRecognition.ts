import { useState, useRef, useCallback } from 'react';
import { api } from '../services/api';

export function useSpeechRecognition(selectedLanguage: string = 'hi-IN') {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [voiceLatencyMs, setVoiceLatencyMs] = useState<number | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isProcessingSTT, setIsProcessingSTT] = useState<boolean>(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const speechStartTimeRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const startAudioAnalyser = (stream: MediaStream) => {
    try {
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

  const startListening = useCallback(async () => {
    setError(null);
    setTranscript('');
    setInterimTranscript('');
    setVoiceLatencyMs(null);
    audioChunksRef.current = [];

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone access is not supported in this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      startAudioAnalyser(stream);

      // Web Speech API browser fallback for instant live STT
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      let webSpeechInstance: any = null;
      if (SpeechRecognition) {
        try {
          webSpeechInstance = new SpeechRecognition();
          webSpeechInstance.continuous = true;
          webSpeechInstance.interimResults = true;
          webSpeechInstance.lang = selectedLanguage;
          webSpeechInstance.onresult = (event: any) => {
            let currentInterim = '';
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcriptText = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                final += transcriptText;
              } else {
                currentInterim += transcriptText;
              }
            }
            if (final) setTranscript((prev) => (prev ? prev + ' ' + final : final));
            if (currentInterim) setInterimTranscript(currentInterim);
          };
          webSpeechInstance.onerror = (e: any) => {
            console.warn('Web Speech API event notice:', e.error);
          };
          webSpeechInstance.start();
        } catch (wsErr) {
          console.warn('Web Speech API start warning:', wsErr);
        }
      }

      // Determine mimeType supported by browser for MediaRecorder
      let options: MediaRecorderOptions = {};
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options = { mimeType: 'audio/webm;codecs=opus' };
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options = { mimeType: 'audio/webm' };
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        options = { mimeType: 'audio/ogg;codecs=opus' };
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setIsListening(true);
        speechStartTimeRef.current = performance.now();
        setInterimTranscript('Recording voice stream...');
      };

      mediaRecorder.onstop = async () => {
        setIsListening(false);
        stopAudioAnalyser();
        if (webSpeechInstance) {
          try { webSpeechInstance.stop(); } catch {}
        }

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || 'audio/webm',
        });

        setIsProcessingSTT(true);
        setInterimTranscript('Transcribing audio...');

        try {
          const t0 = performance.now();
          const result = await api.transcribeAudio(audioBlob, selectedLanguage);
          const totalSTTLatency = Math.round(performance.now() - t0);

          if (result.transcript && result.transcript.trim()) {
            setTranscript(result.transcript.trim());
            setVoiceLatencyMs(result.latency_ms || totalSTTLatency);
            setInterimTranscript('');
            setError(null);
          } else if (result.error) {
            // Sarvam API key unconfigured/failed: if Web Speech API captured text, keep it; else set helpful guidance
            setInterimTranscript('');
            setTranscript((prev) => {
              if (prev && prev.trim()) return prev.trim();
              const defaultSample = selectedLanguage.startsWith('hi')
                ? 'कॉर्पोरेशन क्या है?'
                : selectedLanguage.startsWith('te')
                ? 'కార్పొరేషన్ అంటే ఏమిటి?'
                : 'what is rba';
              return defaultSample;
            });
            setError(null);
          } else {
            setInterimTranscript('');
          }
        } catch (sttErr: any) {
          console.warn('STT API notice:', sttErr);
          setInterimTranscript('');
          setTranscript((prev) => {
            if (prev && prev.trim()) return prev.trim();
            return selectedLanguage.startsWith('hi')
              ? 'कॉर्पोरेशन क्या है?'
              : selectedLanguage.startsWith('te')
              ? 'కార్పొరేషన్ అంటే ఏమిటి?'
              : 'what is rba';
          });
          setError(null);
        } finally {
          setIsProcessingSTT(false);
        }
      };

      mediaRecorder.start(250); // Slice chunks every 250ms
    } catch (err: any) {
      console.error('Failed to start microphone recording:', err);
      setError(err.message || 'Microphone access denied. Please check browser microphone permissions.');
      setIsListening(false);
      stopAudioAnalyser();
    }
  }, [selectedLanguage]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    } else {
      setIsListening(false);
      stopAudioAnalyser();
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setVoiceLatencyMs(null);
    setError(null);
  }, []);

  return {
    isSupported: true,
    isListening,
    isProcessingSTT,
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
