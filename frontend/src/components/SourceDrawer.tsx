import React from 'react';
import { X, FileText, CheckCircle2, Copy } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { SourceItem } from '../types';

interface SourceDrawerProps {
  source: SourceItem | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ source, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!source) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(source.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isGK =
    source.source_type === 'general_knowledge' ||
    source.category_label === 'GENERAL KNOWLEDGE' ||
    source.doc_name.toLowerCase().startsWith('general_knowledge');

  const categoryText = source.category_label || (isGK ? 'GENERAL KNOWLEDGE' : 'POLICY');

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-xs flex justify-end font-mono">
        <motion.div
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 300 }}
          transition={{ type: 'spring', damping: 28, stiffness: 220 }}
          className="w-full max-w-lg bg-[#111311] h-full shadow-2xl flex flex-col border-l border-[rgba(243,235,221,0.14)]"
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-[rgba(243,235,221,0.12)] flex items-center justify-between bg-[#080908]">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-[#171A17] border border-[rgba(243,235,221,0.12)] text-[#F3EBDD]">
                <FileText className="w-4 h-4 text-[#A8D5BA]" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-[#F3EBDD] text-sm leading-tight">
                    {source.doc_name}
                  </h3>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                      isGK
                        ? 'bg-[#123B2A] text-[#A8D5BA] border border-[#1C563E]'
                        : 'bg-[#171A17] text-[#C9C2B5] border border-[rgba(243,235,221,0.12)]'
                    }`}
                  >
                    {categoryText}
                  </span>
                </div>
                <p className="text-[10px] text-[#858983] mt-0.5">
                  CHUNK INDEX #{source.chunk_index} • ID: {source.id}
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#858983] hover:text-[#F3EBDD] hover:bg-[#171A17] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body Stats & Content */}
          <div className="p-6 overflow-y-auto flex-1 space-y-5">
            {/* Metadata Pills */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-[#171A17] rounded-xl border border-[rgba(243,235,221,0.1)]">
                <span className="text-[9px] uppercase tracking-widest text-[#858983] block">
                  SIMILARITY SCORE
                </span>
                <span className="text-lg font-bold text-[#A8D5BA]">
                  {Math.round(source.similarity * 100)}%
                </span>
              </div>

              <div className="p-3 bg-[#171A17] rounded-xl border border-[rgba(243,235,221,0.1)]">
                <span className="text-[9px] uppercase tracking-widest text-[#858983] block">
                  SOURCE TYPE
                </span>
                <span
                  className={`text-xs font-bold inline-block mt-0.5 px-2 py-0.5 rounded ${
                    isGK
                      ? 'bg-[#123B2A] text-[#A8D5BA] border border-[#1C563E]'
                      : 'bg-[#171A17] text-[#C9C2B5] border border-[rgba(243,235,221,0.12)]'
                  }`}
                >
                  {categoryText}
                </span>
              </div>
            </div>

            {/* Chunk Context Text */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#858983]">
                  RETRIEVED CONTEXT PASSAGE
                </h4>
                <button
                  onClick={handleCopy}
                  className="flex items-center space-x-1 text-[11px] text-[#A8D5BA] hover:underline"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-[#A8D5BA]" />
                      <span>COPIED</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>COPY TEXT</span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 rounded-xl bg-[#080908] border border-[rgba(243,235,221,0.12)] text-[#F3EBDD] text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                {source.content}
              </div>
            </div>

            {/* Extra Metadata if available */}
            {source.metadata && Object.keys(source.metadata).length > 0 && (
              <div>
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#858983] mb-2">
                  CHUNK METADATA
                </h4>
                <pre className="p-3 rounded-xl bg-[#080908] border border-[rgba(243,235,221,0.08)] text-[#C9C2B5] text-[11px] overflow-x-auto">
                  {JSON.stringify(source.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-[rgba(243,235,221,0.12)] bg-[#080908] flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#171A17] hover:bg-[#1E231E] text-[#F3EBDD] border border-[rgba(243,235,221,0.14)] rounded-xl text-xs font-semibold transition-colors"
            >
              CLOSE INSPECTOR
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
