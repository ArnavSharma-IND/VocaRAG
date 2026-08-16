import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Upload,
  Trash2,
  RefreshCw,
  FileText,
  CheckCircle2,
  Sliders,
  AlertCircle,
  Eye,
} from 'lucide-react';
import type { DocumentInfo, KnowledgeBaseStats, ChunkInfo } from '../types';
import { api } from '../services/api';

export const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [chunks, setChunks] = useState<ChunkInfo[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isReindexing, setIsReindexing] = useState<boolean>(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Chunking parameters
  const [strategy, setStrategy] = useState<'recursive' | 'fixed' | 'sentence'>('recursive');
  const [chunkSize, setChunkSize] = useState<number>(450);
  const [chunkOverlap, setChunkOverlap] = useState<number>(80);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [docsData, statsData, chunksData] = await Promise.all([
        api.getDocuments(),
        api.getKnowledgeBaseStats(),
        api.getChunks(undefined, 20),
      ]);
      setDocuments(docsData);
      setStats(statsData);
      setChunks(chunksData);
      if (statsData) {
        setStrategy((statsData.chunking_strategy as any) || 'recursive');
        setChunkSize(statsData.chunk_size || 450);
        setChunkOverlap(statsData.chunk_overlap || 80);
      }
    } catch (err: any) {
      console.error('Failed to load KB data:', err);
      setFeedbackMessage({ type: 'error', text: err.message || 'Failed to connect to backend.' });
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setFeedbackMessage(null);

    try {
      for (let i = 0; i < files.length; i++) {
        await api.uploadDocument(files[i]);
      }
      setFeedbackMessage({
        type: 'success',
        text: `Uploaded and indexed ${files.length} document(s).`,
      });
      await loadData();
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Upload failed.' });
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDeleteDocument = async (docId: string, docName: string) => {
    if (!confirm(`Are you sure you want to delete '${docName}'?`)) return;
    try {
      await api.deleteDocument(docId);
      setFeedbackMessage({ type: 'success', text: `Document '${docName}' deleted.` });
      await loadData();
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Delete failed.' });
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    setFeedbackMessage(null);
    try {
      const newStats = await api.reindexKnowledgeBase({
        chunk_strategy: strategy,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      });
      setStats(newStats);
      const updatedChunks = await api.getChunks(selectedDocId || undefined, 20);
      setChunks(updatedChunks);
      const updatedDocs = await api.getDocuments();
      setDocuments(updatedDocs);
      setFeedbackMessage({
        type: 'success',
        text: `Reindexed corpus using ${strategy.toUpperCase()} strategy (${newStats.chunks_count} chunks generated).`,
      });
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Reindexing failed.' });
    } finally {
      setIsReindexing(false);
    }
  };

  const handleFilterChunksByDoc = async (docId: string) => {
    setSelectedDocId(docId);
    try {
      const data = await api.getChunks(docId || undefined, 30);
      setChunks(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-mono">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111311] border border-[rgba(243,235,221,0.12)] text-[#C9C2B5] text-[10px] uppercase tracking-widest mb-2">
            <BookOpen className="w-3 h-3 text-[#1C563E]" />
            <span>EVIDENCE LAYER MANAGEMENT</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F3EBDD] font-mono tracking-tight">
            KNOWLEDGE BASE
          </h1>
          <p className="text-xs text-[#858983] mt-1 font-sans">
            Manage the evidence layer behind VocaRAG. Configure multi-strategy chunking algorithms and rebuild FAISS index.
          </p>
        </div>

        {/* Upload Button */}
        <label className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-[#F3EBDD] hover:bg-[#FFFFFF] text-[#080908] text-xs font-semibold cursor-pointer transition-all hover-lift shadow-md">
          <Upload className="w-3.5 h-3.5 text-[#123B2A]" />
          <span>{isUploading ? 'UPLOADING...' : 'UPLOAD DOCUMENT'}</span>
          <input
            type="file"
            multiple
            accept=".txt,.pdf,.docx,.doc,.md"
            onChange={handleFileUpload}
            disabled={isUploading}
            className="hidden"
          />
        </label>
      </div>

      {/* Feedback Banner */}
      {feedbackMessage && (
        <div
          className={`p-3.5 rounded-2xl mb-6 flex items-center space-x-3 text-xs ${
            feedbackMessage.type === 'success'
              ? 'bg-[#123B2A]/40 text-[#A8D5BA] border border-[#1C563E]'
              : 'bg-[#D58A8A]/10 text-[#D58A8A] border border-[#D58A8A]/30'
          }`}
        >
          {feedbackMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-[#A8D5BA] flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-[#D58A8A] flex-shrink-0" />
          )}
          <span>{feedbackMessage.text}</span>
        </div>
      )}

      {/* Large Minimal Drop Zone */}
      <div className="mb-8 p-8 sm:p-10 rounded-3xl bg-[#111311] border-2 border-dashed border-[rgba(243,235,221,0.14)] hover:border-[#1C563E] text-center transition-colors relative">
        <Upload className="w-8 h-8 text-[#858983] mx-auto mb-3" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-[#F3EBDD] mb-1">
          DROP DOCUMENTS HERE
        </h3>
        <p className="text-[11px] text-[#858983] max-w-sm mx-auto mb-4 font-sans">
          Upload internal policy docs, manuals, handbooks, or general encyclopedias to expand vector grounding.
        </p>
        <div className="flex justify-center space-x-2 text-[10px] text-[#C9C2B5]">
          <span className="px-2 py-0.5 rounded bg-[#171A17] border border-[rgba(243,235,221,0.08)]">PDF</span>
          <span className="px-2 py-0.5 rounded bg-[#171A17] border border-[rgba(243,235,221,0.08)]">TXT</span>
          <span className="px-2 py-0.5 rounded bg-[#171A17] border border-[rgba(243,235,221,0.08)]">DOCX</span>
          <span className="px-2 py-0.5 rounded bg-[#171A17] border border-[rgba(243,235,221,0.08)]">MD</span>
        </div>
      </div>

      {/* Live Technical Stats Readouts */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-8">
        <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[#858983] block mb-1">
            DOCUMENTS
          </span>
          <span className="text-2xl font-bold text-[#F3EBDD]">
            {stats?.documents_count ?? documents.length}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[#858983] block mb-1">
            CHUNKS
          </span>
          <span className="text-2xl font-bold text-[#F3EBDD]">
            {stats?.chunks_count ?? 0}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[#858983] block mb-1">
            EMBEDDINGS
          </span>
          <span className="text-2xl font-bold text-[#F3EBDD]">
            {stats?.embeddings_count ?? 0}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[#858983] block mb-1">
            INDEX STATUS
          </span>
          <span className="text-sm font-bold text-[#A8D5BA] flex items-center space-x-1.5 mt-1.5">
            <span className="w-2 h-2 rounded-full bg-[#1C563E] animate-pulse" />
            <span>READY</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Refined Chunking Controls */}
        <div className="lg:col-span-1 bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] h-fit">
          <div className="flex items-center space-x-2 pb-3 border-b border-[rgba(243,235,221,0.1)] mb-5">
            <Sliders className="w-4 h-4 text-[#1C563E]" />
            <h3 className="font-bold text-[#F3EBDD] text-xs uppercase tracking-widest">
              CHUNKING STRATEGY
            </h3>
          </div>

          {/* Segmented Controls */}
          <div className="mb-5">
            <label className="block text-[10px] uppercase tracking-widest text-[#858983] mb-2">
              ALGORITHM
            </label>
            <div className="grid grid-cols-3 gap-1.5 p-1 bg-[#080908] rounded-xl border border-[rgba(243,235,221,0.1)]">
              {(['fixed', 'sentence', 'recursive'] as const).map((strat) => (
                <button
                  key={strat}
                  type="button"
                  onClick={() => setStrategy(strat)}
                  className={`py-1.5 px-2 rounded-lg text-[10px] uppercase tracking-wider font-semibold transition-all ${
                    strategy === strat
                      ? 'bg-[#171A17] text-[#F3EBDD] border border-[rgba(243,235,221,0.2)]'
                      : 'text-[#858983] hover:text-[#F3EBDD]'
                  }`}
                >
                  {strat}
                </button>
              ))}
            </div>
          </div>

          {/* Chunk Size Slider */}
          <div className="mb-5">
            <div className="flex items-center justify-between text-xs text-[#C9C2B5] mb-2">
              <span className="text-[10px] uppercase tracking-widest text-[#858983]">CHUNK SIZE</span>
              <span className="text-[#A8D5BA]">{chunkSize} chars</span>
            </div>
            <input
              type="range"
              min="150"
              max="1000"
              step="50"
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              className="w-full accent-[#1C563E]"
            />
          </div>

          {/* Overlap Slider */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-xs text-[#C9C2B5] mb-2">
              <span className="text-[10px] uppercase tracking-widest text-[#858983]">OVERLAP</span>
              <span className="text-[#A8D5BA]">{chunkOverlap} chars</span>
            </div>
            <input
              type="range"
              min="0"
              max="250"
              step="10"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(Number(e.target.value))}
              className="w-full accent-[#1C563E]"
            />
          </div>

          {/* Re-Index Trigger */}
          <button
            onClick={handleReindex}
            disabled={isReindexing}
            className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-[#171A17] hover:bg-[#1E231E] text-[#F3EBDD] border border-[rgba(243,235,221,0.18)] text-xs font-semibold transition-all disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#A8D5BA] ${isReindexing ? 'animate-spin' : ''}`} />
            <span>{isReindexing ? 'REBUILDING INDEX...' : 'RE-INDEX KNOWLEDGE BASE'}</span>
          </button>
        </div>

        {/* Right 2 Cols: Document List & Chunk Explorer */}
        <div className="lg:col-span-2 space-y-6">
          {/* Documents Table */}
          <div className="bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] shadow-xl overflow-hidden">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
              <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
                INDEXED DOCUMENTS ({documents.length})
              </h3>
              <span className="text-[10px] text-[#858983]">FAISS INDEXED</span>
            </div>

            {documents.length === 0 ? (
              <div className="p-8 text-center text-[#858983] text-xs">
                NO DOCUMENTS INDEXED. Upload a document to create your evidence layer.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[10px] uppercase tracking-wider text-[#858983] border-b border-[rgba(243,235,221,0.08)] pb-2">
                    <tr>
                      <th className="py-2 px-3">DOCUMENT</th>
                      <th className="py-2 px-3">TYPE</th>
                      <th className="py-2 px-3">CHUNKS</th>
                      <th className="py-2 px-3">STATUS</th>
                      <th className="py-2 px-3 text-right">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[rgba(243,235,221,0.06)]">
                    {documents.map((doc) => {
                      const isGK = doc.name.toLowerCase().startsWith('general_knowledge') || doc.category_badge === 'GENERAL';
                      return (
                        <tr key={doc.id} className="hover:bg-[#171A17]/60 transition-colors">
                          <td className="py-3 px-3 text-[#F3EBDD] font-medium flex items-center space-x-2">
                            <FileText className="w-3.5 h-3.5 text-[#1C563E] flex-shrink-0" />
                            <span className="truncate max-w-xs">{doc.name}</span>
                          </td>
                          <td className="py-3 px-3">
                            {isGK ? (
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#123B2A] text-[#A8D5BA] border border-[#1C563E]">
                                GENERAL
                              </span>
                            ) : doc.is_sample ? (
                              <span className="px-2 py-0.5 rounded text-[9px] font-medium bg-[#171A17] text-[#C9C2B5] border border-[rgba(243,235,221,0.12)]">
                                SAMPLE
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[9px] font-medium bg-[#171A17] text-[#D9C48A] border border-[#D9C48A]/30">
                                UPLOAD
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-[#A8D5BA] font-bold">
                            {doc.chunks_count}
                          </td>
                          <td className="py-3 px-3">
                            <span className="text-[10px] text-[#A8D5BA] font-bold">READY</span>
                          </td>
                          <td className="py-3 px-3 text-right space-x-1">
                            <button
                              onClick={() => handleFilterChunksByDoc(doc.id)}
                              title="Inspect Chunks"
                              className="p-1 text-[#858983] hover:text-[#F3EBDD] transition-colors"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(doc.id, doc.name)}
                              title="Delete Document"
                              className="p-1 text-[#D58A8A] hover:text-red-400 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Chunk Preview Explorer */}
          <div className="bg-[#111311] rounded-3xl p-6 border border-[rgba(243,235,221,0.14)] shadow-xl">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(243,235,221,0.08)]">
              <h3 className="font-bold text-xs uppercase tracking-widest text-[#858983]">
                CHUNK EXPLORER {selectedDocId && `(${selectedDocId})`}
              </h3>

              {selectedDocId && (
                <button
                  onClick={() => handleFilterChunksByDoc('')}
                  className="text-[10px] text-[#A8D5BA] hover:underline"
                >
                  SHOW ALL
                </button>
              )}
            </div>

            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {chunks.map((chk, idx) => (
                <div
                  key={chk.id || idx}
                  className="p-3 rounded-2xl bg-[#080908] border border-[rgba(243,235,221,0.08)] text-xs"
                >
                  <div className="flex items-center justify-between text-[#858983] mb-1.5">
                    <span className="text-[#F3EBDD] font-bold text-[11px]">
                      {chk.doc_name} • Chunk #{chk.chunk_index}
                    </span>
                    <span className="text-[10px] text-[#A8D5BA]">
                      {chk.char_count} chars
                    </span>
                  </div>
                  <p className="text-[#C9C2B5] leading-relaxed font-sans text-xs">{chk.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
