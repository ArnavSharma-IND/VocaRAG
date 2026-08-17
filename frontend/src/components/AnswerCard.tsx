import React, { useState, useRef } from 'react';
import { ArrowUpRight, Info, Volume2, Square, Award } from 'lucide-react';
import { motion } from 'framer-motion';
import type { AskResponse, SourceItem } from '../types';
import { SourceDrawer } from './SourceDrawer';
import { api } from '../services/api';

interface AnswerCardProps {
  response: AskResponse;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ response }) => {
  const [selectedSource, setSelectedSource] = useState<SourceItem | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [isSynthesizingTTS, setIsSynthesizingTTS] = useState<boolean>(false);
  const [ttsError, setTtsError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { query, answer, abstained, confidence, sources, retrieval_explanation } = response;

  const hasGoldPassage = sources.some(s => s.metadata?.is_selected === true || s.metadata?.is_selected === 1);

  const handlePlayTTS = async () => {
    if (isPlayingAudio && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlayingAudio(false);
      return;
    }

    setTtsError(null);
    setIsSynthesizingTTS(true);

    try {
      // Determine language code based on source language or query characters
      let targetLang = 'hi-IN';
      const hasTelugu = /[\u0C00-\u0C7F]/.test(answer) || /[\u0C00-\u0C7F]/.test(query);
      const hasHindi = /[\u0900-\u097F]/.test(answer) || /[\u0900-\u097F]/.test(query);

      if (hasTelugu) targetLang = 'te-IN';
      else if (hasHindi) targetLang = 'hi-IN';
      else targetLang = 'en-IN';

      const ttsResult = await api.synthesizeSpeech(answer, targetLang, 'meera');

      if (ttsResult.audio_base64) {
        const audioSrc = `data:${ttsResult.content_type || 'audio/wav'};base64,${ttsResult.audio_base64}`;
        const audio = new Audio(audioSrc);
        audioRef.current = audio;

        audio.onplay = () => setIsPlayingAudio(true);
        audio.onended = () => setIsPlayingAudio(false);
        audio.onerror = () => {
          setIsPlayingAudio(false);
          setTtsError('Audio playback failed.');
        };

        await audio.play();
      } else {
        setTtsError(ttsResult.error || 'TTS audio generation failed.');
      }
    } catch (err: any) {
      console.error('TTS error:', err);
      setTtsError(err.message || 'Could not connect to Sarvam Bulbul TTS');
    } finally {
      setIsSynthesizingTTS(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 sm:p-8 rounded-3xl bg-[#111311] border border-[rgba(243,235,221,0.14)] shadow-2xl space-y-6 font-sans"
    >
      {/* Top Header & Badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[rgba(243,235,221,0.08)] pb-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-semibold text-[#858983] uppercase tracking-wider">
            ANSWER
          </span>
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
            abstained ? 'bg-[#D9C48A]/20 text-[#D9C48A]' : 'bg-[#1C563E] text-[#A8D5BA]'
          }`}>
            {abstained ? 'ABSTAINED' : 'GROUNDED'}
          </span>
          {hasGoldPassage && (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-[#D9C48A]/20 text-[#D9C48A] border border-[#D9C48A]/30 flex items-center gap-1">
              <Award className="w-3 h-3" />
              <span>MS MARCO GOLD MATCH</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* Sarvam Bulbul TTS Voice Button */}
          <button
            onClick={handlePlayTTS}
            disabled={isSynthesizingTTS}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              isPlayingAudio
                ? 'bg-[#1C563E] text-[#F3EBDD] animate-pulse shadow-md'
                : 'bg-[#171A17] hover:bg-[#1E231E] text-[#A8D5BA] border border-[rgba(243,235,221,0.12)]'
            }`}
          >
            {isSynthesizingTTS ? (
              <div className="w-3.5 h-3.5 border-2 border-[#A8D5BA] border-t-transparent rounded-full animate-spin" />
            ) : isPlayingAudio ? (
              <Square className="w-3.5 h-3.5 fill-current" />
            ) : (
              <Volume2 className="w-3.5 h-3.5" />
            )}
            <span>
              {isSynthesizingTTS
                ? 'SYNTHESIZING (BULBUL)...'
                : isPlayingAudio
                ? 'STOP VOICE'
                : 'LISTEN ANSWER (BULBUL TTS)'}
            </span>
          </button>

          <span className="text-xs text-[#858983] font-mono">
            CONFIDENCE: <strong className="text-[#F3EBDD]">{Math.round(confidence * 100)}%</strong>
          </span>
        </div>
      </div>

      {/* TTS Error Banner */}
      {ttsError && (
        <div className="text-xs text-[#D58A8A] bg-[#D58A8A]/10 px-3 py-1.5 rounded-lg font-mono">
          {ttsError}
        </div>
      )}

      {/* Answer Body */}
      <div className="space-y-4">
        <div className="text-base sm:text-lg text-[#F3EBDD] leading-relaxed font-serif whitespace-pre-wrap">
          {answer}
        </div>
      </div>

      {/* Retrieval Explanation */}
      {retrieval_explanation && (
        <div className="p-4 rounded-2xl bg-[#171A17] border border-[rgba(243,235,221,0.06)] flex items-start space-x-2.5 text-xs text-[#858983]">
          <Info className="w-4 h-4 text-[#A8D5BA] flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">{retrieval_explanation}</p>
        </div>
      )}

      {/* Retrieved Sources Citation Carousel/Pills */}
      {sources.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-[rgba(243,235,221,0.08)]">
          <span className="text-[10px] text-[#858983] uppercase tracking-wider font-mono">
            EVIDENCE CITATIONS ({sources.length}):
          </span>
          <div className="flex flex-wrap gap-2">
            {sources.map((src, idx) => {
              const isGold = src.metadata?.is_selected === true || src.metadata?.is_selected === 1;
              return (
                <button
                  key={src.id || idx}
                  onClick={() => setSelectedSource(src)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono transition-all hover-lift ${
                    isGold
                      ? 'bg-[#1C563E]/40 border-[#D9C48A]/50 text-[#F3EBDD]'
                      : 'bg-[#171A17] hover:bg-[#1E231E] border-[rgba(243,235,221,0.12)] text-[#C9C2B5]'
                  }`}
                >
                  {isGold && <Award className="w-3 h-3 text-[#D9C48A]" />}
                  <span className="font-semibold text-[#A8D5BA]">[Source {idx + 1}]</span>
                  <span className="truncate max-w-[140px]">{src.doc_name}</span>
                  <span className="text-[#858983]">({Math.round(src.similarity * 100)}%)</span>
                  <ArrowUpRight className="w-3 h-3 text-[#858983]" />
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Drawer */}
      <SourceDrawer source={selectedSource} onClose={() => setSelectedSource(null)} />
    </motion.div>
  );
};
