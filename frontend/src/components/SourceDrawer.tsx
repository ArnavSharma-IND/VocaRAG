import React from 'react';
import { X, FileText, CheckCircle2, Copy, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { SourceItem } from '../types';

interface SourceDrawerProps {
  source: SourceItem | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ source, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!source) return null;

  const isGoldPassage = source.metadata?.is_selected === true || source.metadata?.is_selected === 1;

  const handleCopy = () => {
    navigator.clipboard.writeText(source.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        />

        <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="w-screen max-w-md bg-[#111311] border-l border-[rgba(243,235,221,0.12)] shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="p-6 border-b border-[rgba(243,235,221,0.08)] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-[#A8D5BA]" />
                <h2 className="text-sm font-semibold text-[#F3EBDD] truncate max-w-[240px]">
                  {source.doc_name}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="p-1 text-[#858983] hover:text-[#F3EBDD] rounded-lg hover:bg-[#171A17] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Gold Passage Banner */}
            {isGoldPassage && (
              <div className="px-6 py-3 bg-[#1C563E]/30 border-b border-[#1C563E]/40 flex items-center space-x-2">
                <Award className="w-4 h-4 text-[#D9C48A] flex-shrink-0" />
                <div>
                  <span className="text-xs font-bold text-[#F3EBDD] flex items-center gap-1.5">
                    <span>✓ MS MARCO Gold Passage</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#D9C48A]/20 text-[#D9C48A] uppercase font-mono">
                      Ground Truth
                    </span>
                  </span>
                  <p className="text-[10px] text-[#A8D5BA] mt-0.5">
                    Human-verified relevant passage from AI4Bharat MSMARCO-XI dataset.
                  </p>
                </div>
              </div>
            )}

            {/* Content Body */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {/* Metadata Badges */}
              <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                <span className="px-2.5 py-1 rounded bg-[#171A17] border border-[rgba(243,235,221,0.1)] text-[#A8D5BA]">
                  SIMILARITY: {Math.round(source.similarity * 100)}%
                </span>
                <span className="px-2.5 py-1 rounded bg-[#171A17] border border-[rgba(243,235,221,0.1)] text-[#D9C48A]">
                  TIER: {source.relevance_tier.toUpperCase()}
                </span>
                <span className="px-2.5 py-1 rounded bg-[#171A17] border border-[rgba(243,235,221,0.1)] text-[#858983]">
                  CHUNK #{source.chunk_index}
                </span>
                {source.metadata?.passage_id && (
                  <span className="px-2.5 py-1 rounded bg-[#171A17] border border-[rgba(243,235,221,0.1)] text-[#F3EBDD]">
                    PASSAGE: {source.metadata.passage_id}
                  </span>
                )}
                {source.metadata?.language && (
                  <span className="px-2.5 py-1 rounded bg-[#171A17] border border-[rgba(243,235,221,0.1)] text-[#A8D5BA] uppercase">
                    LANG: {source.metadata.language}
                  </span>
                )}
              </div>

              {/* Passage Full Content */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wider text-[#858983] font-mono">
                    Retrieved Passage Content
                  </span>
                  <button
                    onClick={handleCopy}
                    className="flex items-center space-x-1 text-xs text-[#858983] hover:text-[#F3EBDD] transition-colors"
                  >
                    {copied ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#A8D5BA]" />
                        <span className="text-[#A8D5BA]">COPIED</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>COPY TEXT</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="p-4 bg-[#171A17] rounded-2xl border border-[rgba(243,235,221,0.08)] text-sm text-[#F3EBDD] font-serif leading-relaxed whitespace-pre-wrap">
                  {source.content}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </AnimatePresence>
  );
};
