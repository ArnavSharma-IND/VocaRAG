import React, { useState, useEffect } from 'react';
import { Mic, Send, RotateCcw, Keyboard, Volume2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

interface VoiceHeroProps {
  onSubmitQuery: (query: string, voiceLatencyMs?: number) => void;
  isLoading: boolean;
  activeQuery: string;
}

export const VoiceHero: React.FC<VoiceHeroProps> = ({
  onSubmitQuery,
  isLoading,
  activeQuery,
}) => {
  const {
    isListening,
    transcript,
    interimTranscript,
    error: speechError,
    voiceLatencyMs,
    audioLevel,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition();

  const [inputQuery, setInputQuery] = useState<string>('');
  const [isTypingMode, setIsTypingMode] = useState<boolean>(false);

  // Sync speech transcript into input field
  useEffect(() => {
    if (transcript) {
      setInputQuery(transcript);
    }
  }, [transcript]);

  // If activeQuery is changed externally
  useEffect(() => {
    if (activeQuery) {
      setInputQuery(activeQuery);
    }
  }, [activeQuery]);

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      resetTranscript();
      setInputQuery('');
      startListening();
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    if (isListening) stopListening();
    onSubmitQuery(inputQuery.trim(), voiceLatencyMs || undefined);
  };

  const handleSuggestionClick = (text: string) => {
    setInputQuery(text);
    if (isListening) stopListening();
  };

  const sampleSuggestions = [
    'What is the refund period for hardware purchases?',
    'What is photosynthesis?',
    'What is an API?',
    'What is the capital of India?',
    'Why is the sky blue?',
    'What is the laptop loss procedure?',
  ];

  // Dynamic state label
  const stateLabel = isListening
    ? 'LISTENING'
    : isLoading
    ? 'PROCESSING'
    : inputQuery
    ? 'QUERY RECEIVED'
    : 'READY TO LISTEN';

  return (
    <section className="relative pt-8 pb-10 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto text-center font-mono">
      {/* Eyebrow & Hero Display Headline */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#C9C2B5] text-[10px] uppercase tracking-widest mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1C563E]" />
          <span>VOICE-ENABLED INTELLIGENCE</span>
        </div>

        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#F3EBDD] leading-tight">
          Speak a question.
          <br />
          <span className="text-[#C9C2B5]">Get a grounded answer.</span>
        </h1>

        <p className="mt-3 text-xs sm:text-sm text-[#858983] max-w-xl mx-auto font-sans">
          Natural speech input coupled with multi-strategy FAISS retrieval across Enterprise Documents & General Knowledge.
        </p>
      </motion.div>

      {/* Central Precision Microphone Instrument */}
      <div className="mt-10 relative max-w-3xl mx-auto">
        <div className="bg-[#111311] rounded-3xl p-6 sm:p-8 border border-[rgba(243,235,221,0.14)] shadow-2xl relative overflow-hidden">
          {/* Subtle Background Technical Radial Glow */}
          <div className="absolute inset-0 radial-vignette pointer-events-none" />

          <div className="relative z-10 flex flex-col items-center">
            {/* Precision Circular Mic Instrument */}
            {!isTypingMode && (
              <div className="my-2 flex flex-col items-center">
                <div className="relative flex items-center justify-center p-3">
                  {/* Outer Concentric Technical Ring */}
                  <div
                    className={`absolute w-32 h-32 sm:w-36 sm:h-36 rounded-full border border-dashed transition-all ${
                      isListening
                        ? 'border-[#B45A7A] animate-spin'
                        : 'border-[rgba(243,235,221,0.18)] animate-breathe'
                    }`}
                  />

                  {/* Pulsing Ripple Waves on active listening */}
                  {isListening && (
                    <>
                      <div className="absolute w-40 h-40 rounded-full bg-[#123B2A]/40 animate-ping" />
                      <div className="absolute w-36 h-36 rounded-full bg-[#1C563E]/30" />
                    </>
                  )}

                  {/* Center Control Button */}
                  <button
                    onClick={handleMicClick}
                    disabled={isLoading}
                    aria-label={isListening ? 'Stop listening' : 'Start speaking'}
                    className={`relative z-20 w-24 h-24 sm:w-28 sm:h-28 rounded-full flex flex-col items-center justify-center transition-all transform active:scale-95 border ${
                      isListening
                        ? 'bg-[#123B2A] border-[#1C563E] text-[#F3EBDD] shadow-[0_0_24px_rgba(28,86,62,0.6)]'
                        : 'bg-[#171A17] hover:bg-[#1E231E] border-[rgba(243,235,221,0.22)] text-[#F3EBDD]'
                    }`}
                  >
                    <Mic
                      className={`w-9 h-9 sm:w-10 sm:h-10 transition-colors ${
                        isListening ? 'text-[#A8D5BA] animate-pulse' : 'text-[#F3EBDD]'
                      }`}
                    />
                    <span className="text-[9px] mt-1 text-[#858983] uppercase tracking-wider">
                      {isListening ? 'STOP' : 'MIC'}
                    </span>
                  </button>
                </div>

                {/* State Label & Live Waveform Indicator */}
                <div className="mt-4 flex flex-col items-center">
                  <div className="flex items-center space-x-2">
                    {isListening && (
                      <div className="flex items-end space-x-1 h-5 mr-1">
                        <div className="w-1 bg-[#A8D5BA] rounded-full wave-bar-1" />
                        <div className="w-1 bg-[#A8D5BA] rounded-full wave-bar-2" />
                        <div className="w-1 bg-[#A8D5BA] rounded-full wave-bar-3" />
                        <div className="w-1 bg-[#A8D5BA] rounded-full wave-bar-4" />
                        <div className="w-1 bg-[#A8D5BA] rounded-full wave-bar-5" />
                      </div>
                    )}
                    <span
                      className={`text-[11px] uppercase tracking-widest font-semibold ${
                        isListening
                          ? 'text-[#A8D5BA] animate-pulse'
                          : isLoading
                          ? 'text-[#D9C48A]'
                          : 'text-[#858983]'
                      }`}
                    >
                      {stateLabel} {audioLevel > 0 ? `(${audioLevel}%)` : ''}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Speech Recognition Error Notice if any */}
            {speechError && (
              <div className="mt-3 flex items-center space-x-2 text-xs text-[#D58A8A] bg-[#D58A8A]/10 px-3 py-1.5 rounded-lg border border-[#D58A8A]/20">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{speechError}</span>
              </div>
            )}

            {/* Live Interim Speech Preview */}
            <AnimatePresence>
              {isListening && interimTranscript && (
                <motion.p
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-2 text-xs text-[#C9C2B5] italic max-w-lg"
                >
                  “{interimTranscript}”
                </motion.p>
              )}
            </AnimatePresence>

            {/* Transcript & Editorial Input Box */}
            <form onSubmit={handleFormSubmit} className="w-full mt-5">
              <div className="relative">
                <textarea
                  rows={2}
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder={
                    isListening
                      ? 'Listening to voice stream...'
                      : 'Speak via microphone or enter query directly...'
                  }
                  className="w-full px-4 py-3 sm:py-3.5 text-sm sm:text-base text-[#F3EBDD] bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.14)] focus:outline-none focus:border-[#1C563E] focus:ring-1 focus:ring-[#1C563E] resize-none transition-all placeholder-[#858983] font-sans"
                />

                <div className="absolute left-3.5 -top-2.5 px-2 py-0.5 bg-[#111311] border border-[rgba(243,235,221,0.14)] rounded text-[9px] uppercase tracking-widest text-[#858983]">
                  VOICE INPUT
                </div>

                {voiceLatencyMs && (
                  <div className="absolute right-3 top-3 text-[10px] px-2 py-0.5 rounded bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#A8D5BA]">
                    STT: {voiceLatencyMs}ms
                  </div>
                )}
              </div>

              {/* Action Buttons: Ask VocaRAG, Clear, Type Instead */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setIsTypingMode(!isTypingMode)}
                  className="flex items-center space-x-1.5 text-xs text-[#858983] hover:text-[#F3EBDD] transition-colors"
                >
                  {isTypingMode ? (
                    <>
                      <Volume2 className="w-3.5 h-3.5 text-[#1C563E]" />
                      <span>USE VOICE INPUT</span>
                    </>
                  ) : (
                    <>
                      <Keyboard className="w-3.5 h-3.5 text-[#858983]" />
                      <span>TYPE INSTEAD</span>
                    </>
                  )}
                </button>

                <div className="flex items-center space-x-2.5 ml-auto">
                  {inputQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setInputQuery('');
                        resetTranscript();
                      }}
                      className="flex items-center space-x-1 px-3 py-2 rounded-xl text-xs text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17] transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>CLEAR</span>
                    </button>
                  )}

                  <button
                    type="submit"
                    disabled={!inputQuery.trim() || isLoading}
                    className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#F3EBDD] hover:bg-[#FFFFFF] text-[#080908] shadow-md transition-all transform active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed hover-lift"
                  >
                    {isLoading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-3.5 h-3.5 border-2 border-[#080908] border-t-transparent rounded-full animate-spin" />
                        <span>PROCESSING...</span>
                      </div>
                    ) : (
                      <>
                        <Send className="w-3.5 h-3.5 text-[#123B2A]" />
                        <span>ASK VOCARAG</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Suggestion Chips */}
        <div className="mt-6 text-left">
          <p className="text-[10px] uppercase tracking-widest text-[#858983] mb-2 px-1">
            TEST QUESTIONS (POLICIES & GENERAL KNOWLEDGE):
          </p>
          <div className="flex flex-wrap gap-2">
            {sampleSuggestions.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(item)}
                className="text-left text-xs bg-[#111311] hover:bg-[#171A17] text-[#C9C2B5] hover:text-[#F3EBDD] px-3 py-1.5 rounded-xl border border-[rgba(243,235,221,0.12)] transition-all hover-lift"
              >
                “{item}”
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
