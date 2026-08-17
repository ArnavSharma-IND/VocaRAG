import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, RotateCcw, Keyboard, Volume2, AlertCircle, Globe, Layers, ArrowRightLeft } from 'lucide-react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

interface VoiceHeroProps {
  onAsk: (query: string, voiceLatencyMs?: number, collection?: string) => void;
  isLoading: boolean;
  initialQuery?: string;
  activeCollection?: string;
  onCollectionChange?: (col: string) => void;
}

const INDIC_SUGGESTIONS = [
  "भारत की राजधानी क्या है?",
  "प्रकाश संश्लेषण क्या है?",
  "భారతదేశ రాజధాని ఏది?",
  "What is photosynthesis?",
  "What is the capital of India?",
  "What is the population of planet Xylon-9?"
];

const ENTERPRISE_SUGGESTIONS = [
  "What is the annual leave allowance for employees?",
  "What is the standard refund period for hardware?",
  "What should I do immediately if I lose my laptop?",
  "What is the anonymous ethics whistleblower phone number?",
  "What is the company policy on offshore cryptocurrency trading?"
];

export const VoiceHero: React.FC<VoiceHeroProps> = ({
  onAsk,
  isLoading,
  initialQuery = '',
  activeCollection = 'msmarco',
  onCollectionChange
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('hi-IN');
  const [sttMode, setSttMode] = useState<string>('transcribe'); // transcribe | translate
  const [collection, setCollection] = useState<string>(activeCollection);
  const [inputQuery, setInputQuery] = useState<string>(initialQuery);
  const [isTypingMode, setIsTypingMode] = useState<boolean>(false);

  const {
    isListening,
    isProcessingSTT,
    transcript,
    interimTranscript,
    error: speechError,
    voiceLatencyMs,
    audioLevel,
    startListening,
    stopListening,
    resetTranscript,
    setTranscript,
  } = useSpeechRecognition(selectedLanguage);

  useEffect(() => {
    if (initialQuery) {
      setInputQuery(initialQuery);
      setTranscript(initialQuery);
    }
  }, [initialQuery, setTranscript]);

  useEffect(() => {
    if (transcript) {
      setInputQuery(transcript);
    }
  }, [transcript]);

  const handleCollectionSwitch = (newCol: string) => {
    setCollection(newCol);
    if (onCollectionChange) onCollectionChange(newCol);
  };

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
    onAsk(inputQuery.trim(), voiceLatencyMs || undefined, collection);
  };

  const handleSuggestionClick = (query: string) => {
    setInputQuery(query);
    setTranscript(query);
    onAsk(query, undefined, collection);
  };

  const stateLabel = isListening
    ? 'LISTENING VIA MEDIA RECORDER'
    : isProcessingSTT
    ? `TRANSCRIBING (${sttMode === 'translate' ? 'SARVAM TRANSLATE MODE' : 'SARVAM SAARAS V3'})...`
    : isLoading
    ? 'PROCESSING RAG PIPELINE...'
    : 'CLICK MIC TO SPEAK IN INDIC OR ENGLISH';

  const currentSuggestions = collection === 'msmarco' ? INDIC_SUGGESTIONS : ENTERPRISE_SUGGESTIONS;

  return (
    <section className="relative pt-6 pb-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center">
      {/* Top Mode Selectors: Collection & Language & STT Mode */}
      <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
        {/* Collection Selector Tabs */}
        <div className="inline-flex p-1 bg-[#111311] rounded-xl border border-[rgba(243,235,221,0.12)]">
          <button
            type="button"
            onClick={() => handleCollectionSwitch('msmarco')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              collection === 'msmarco'
                ? 'bg-[#1C563E] text-[#F3EBDD] shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Indic MSMARCO-XI (Graded)</span>
          </button>
          <button
            type="button"
            onClick={() => handleCollectionSwitch('enterprise')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              collection === 'enterprise'
                ? 'bg-[#1C563E] text-[#F3EBDD] shadow-sm'
                : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Enterprise Policies (Demo)</span>
          </button>
        </div>

        {/* Sarvam STT Language Selector */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#111311] rounded-xl border border-[rgba(243,235,221,0.12)] text-xs text-[#858983]">
          <span className="font-mono text-[10px] text-[#A8D5BA] uppercase">Sarvam STT:</span>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="bg-transparent text-[#F3EBDD] font-medium focus:outline-none cursor-pointer"
          >
            <option value="hi-IN" className="bg-[#111311] text-[#F3EBDD]">Hindi (हिन्दी / hi-IN)</option>
            <option value="te-IN" className="bg-[#111311] text-[#F3EBDD]">Telugu (తెలుగు / te-IN)</option>
            <option value="en-IN" className="bg-[#111311] text-[#F3EBDD]">English (Indian / en-IN)</option>
            <option value="bn-IN" className="bg-[#111311] text-[#F3EBDD]">Bengali (বাংলা / bn-IN)</option>
          </select>
        </div>

        {/* STT Translate Mode Switcher */}
        <div className="inline-flex p-1 bg-[#111311] rounded-xl border border-[rgba(243,235,221,0.12)]">
          <button
            type="button"
            onClick={() => setSttMode('transcribe')}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all ${
              sttMode === 'transcribe'
                ? 'bg-[#1C563E] text-[#F3EBDD]'
                : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <span>Direct STT</span>
          </button>
          <button
            type="button"
            onClick={() => setSttMode('translate')}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all ${
              sttMode === 'translate'
                ? 'bg-[#1C563E] text-[#F3EBDD]'
                : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <ArrowRightLeft className="w-3 h-3" />
            <span>Indic $\to$ English Pivot</span>
          </button>
        </div>
      </div>

      {/* Main Mic & Query Card */}
      <div className="relative rounded-3xl p-6 sm:p-8 border border-[rgba(243,235,221,0.14)] bg-[#0C241B]/20 backdrop-blur-xl shadow-2xl overflow-hidden">
        <div className="max-w-2xl mx-auto flex flex-col items-center">
          {/* Circular Microphone Button with Pulsing Waveform Ring */}
          {!isTypingMode && (
            <div className="relative mb-4 flex flex-col items-center">
              <div className="relative flex items-center justify-center">
                {isListening && (
                  <>
                    <motion.div
                      animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0.1, 0.6] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="absolute w-28 h-28 sm:w-32 sm:h-32 rounded-full bg-[#1C563E]/40"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1], opacity: [0.8, 0.2, 0.8] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="absolute w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-[#A8D5BA]/20"
                    />
                  </>
                )}

                <button
                  type="button"
                  onClick={handleMicClick}
                  disabled={isLoading || isProcessingSTT}
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
                  <span className="text-[9px] mt-1 text-[#858983] uppercase tracking-wider font-mono">
                    {isListening ? 'STOP' : 'SARVAM MIC'}
                  </span>
                </button>
              </div>

              {/* Status State & Wave Indicator */}
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
                    className={`text-[11px] uppercase tracking-widest font-semibold font-mono ${
                      isListening
                        ? 'text-[#A8D5BA] animate-pulse'
                        : isProcessingSTT || isLoading
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

          {/* Speech Error Banner */}
          {speechError && (
            <div className="mt-3 flex items-center space-x-2 text-xs text-[#D58A8A] bg-[#D58A8A]/10 px-3 py-1.5 rounded-lg border border-[#D58A8A]/20">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{speechError}</span>
            </div>
          )}

          {/* Live Interim Transcript */}
          <AnimatePresence>
            {(isListening || isProcessingSTT) && interimTranscript && (
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

          {/* Transcript & Query Box */}
          <form onSubmit={handleFormSubmit} className="w-full mt-4">
            <div className="relative">
              <textarea
                rows={2}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  isListening
                    ? 'Listening... Speak in Hindi, Telugu, or English...'
                    : 'Speak via Sarvam AI mic or type query here...'
                }
                className="w-full px-4 py-3 sm:py-3.5 text-sm sm:text-base text-[#F3EBDD] bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.14)] focus:outline-none focus:border-[#1C563E] focus:ring-1 focus:ring-[#1C563E] resize-none transition-all placeholder-[#858983] font-sans"
              />

              <div className="absolute left-3.5 -top-2.5 px-2 py-0.5 bg-[#111311] border border-[rgba(243,235,221,0.14)] rounded text-[9px] uppercase tracking-widest text-[#858983] font-mono">
                {collection === 'msmarco' ? 'INDIC MSMARCO QUERY' : 'ENTERPRISE QUERY'}
              </div>

              {voiceLatencyMs && (
                <div className="absolute right-3 top-3 text-[10px] px-2 py-0.5 rounded bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#A8D5BA] font-mono">
                  SARVAM STT: {voiceLatencyMs}ms
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setIsTypingMode(!isTypingMode)}
                className="flex items-center space-x-1.5 text-xs text-[#858983] hover:text-[#F3EBDD] transition-colors"
              >
                {isTypingMode ? (
                  <>
                    <Volume2 className="w-3.5 h-3.5 text-[#1C563E]" />
                    <span>USE SARVAM VOICE</span>
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

      {/* Suggested Questions */}
      <div className="mt-6 text-left">
        <p className="text-[10px] uppercase tracking-widest text-[#858983] mb-2 px-1 font-mono">
          TEST QUERIES ({collection === 'msmarco' ? 'INDIC MSMARCO-XI' : 'ENTERPRISE POLICIES'}):
        </p>
        <div className="flex flex-wrap gap-2">
          {currentSuggestions.map((item, idx) => (
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
    </section>
  );
};
