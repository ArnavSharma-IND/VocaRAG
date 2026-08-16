import React, { useState, useEffect } from 'react';
import { Upload, Trash2, RefreshCw, Database, Layers, Globe } from 'lucide-react';
import { api } from '../services/api';
import type { DocumentInfo, KnowledgeBaseStats } from '../types';

export const KnowledgeBasePage: React.FC = () => {
  const [collection, setCollection] = useState<string>('msmarco');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isReindexing, setIsReindexing] = useState<boolean>(false);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('recursive');
  const [chunkSize, setChunkSize] = useState<number>(450);
  const [chunkOverlap, setChunkOverlap] = useState<number>(80);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  useEffect(() => {
    loadData(collection);
  }, [collection]);

  const loadData = async (col: string) => {
    setIsLoading(true);
    try {
      const [docs, st] = await Promise.all([
        api.getDocuments(col),
        api.getKnowledgeBaseStats(col)
      ]);
      setDocuments(docs);
      setStats(st);
      if (st) {
        setSelectedStrategy(st.chunking_strategy);
        setChunkSize(st.chunk_size);
        setChunkOverlap(st.chunk_overlap);
      }
    } catch (err) {
      console.error('Failed to load KB data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus(`Uploading and indexing ${file.name}...`);
    try {
      await api.uploadDocument(file, collection);
      setUploadStatus(`Successfully uploaded and indexed ${file.name}!`);
      loadData(collection);
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message}`);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await api.deleteDocument(docId, collection);
      loadData(collection);
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      const newStats = await api.reindexKnowledgeBase({
        chunk_strategy: selectedStrategy,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap
      }, collection);
      setStats(newStats);
      loadData(collection);
    } catch (err) {
      console.error('Reindex failed:', err);
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header & Collection Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[rgba(243,235,221,0.12)] pb-6">
        <div>
          <h1 className="text-2xl font-bold font-editorial text-[#F3EBDD]">Knowledge Base & Index Studio</h1>
          <p className="text-xs text-[#858983] mt-1 font-mono">
            Manage multi-format documents, chunking strategies, and FAISS vector indices.
          </p>
        </div>

        {/* Collection Selector */}
        <div className="inline-flex p-1 bg-[#111311] rounded-xl border border-[rgba(243,235,221,0.12)]">
          <button
            onClick={() => setCollection('msmarco')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              collection === 'msmarco' ? 'bg-[#1C563E] text-[#F3EBDD]' : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Indic MSMARCO-XI</span>
          </button>
          <button
            onClick={() => setCollection('enterprise')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              collection === 'enterprise' ? 'bg-[#1C563E] text-[#F3EBDD]' : 'text-[#858983] hover:text-[#F3EBDD]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Enterprise Policies</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono">
          <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.1)]">
            <span className="text-[10px] text-[#858983] uppercase tracking-wider">DOCUMENTS</span>
            <p className="text-xl font-bold text-[#F3EBDD] mt-1">{stats.documents_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.1)]">
            <span className="text-[10px] text-[#858983] uppercase tracking-wider">CHUNKS</span>
            <p className="text-xl font-bold text-[#A8D5BA] mt-1">{stats.chunks_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.1)]">
            <span className="text-[10px] text-[#858983] uppercase tracking-wider">FAISS VECTORS</span>
            <p className="text-xl font-bold text-[#D9C48A] mt-1">{stats.embeddings_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.1)]">
            <span className="text-[10px] text-[#858983] uppercase tracking-wider">DIMENSION</span>
            <p className="text-xl font-bold text-[#F3EBDD] mt-1">{stats.embedding_dimension}D</p>
          </div>
        </div>
      )}

      {/* Reindexing Controls */}
      <div className="p-6 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)] space-y-4">
        <h2 className="text-sm font-semibold text-[#F3EBDD] uppercase tracking-wider font-mono flex items-center space-x-2">
          <Database className="w-4 h-4 text-[#A8D5BA]" />
          <span>Chunking Strategy & Parameter Studio</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-[#858983] block mb-1 font-mono">Strategy:</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 bg-[#171A17] text-[#F3EBDD] rounded-xl border border-[rgba(243,235,221,0.14)] text-xs focus:outline-none"
            >
              <option value="recursive">Recursive Hierarchical (Default)</option>
              <option value="semantic">Semantic (Embedding-Similarity)</option>
              <option value="sentence">Sentence Grouping</option>
              <option value="fixed">Fixed-Size Word Snapping</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-[#858983] block mb-1 font-mono">Chunk Size (chars):</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(parseInt(e.target.value) || 450)}
              className="w-full px-3 py-2 bg-[#171A17] text-[#F3EBDD] rounded-xl border border-[rgba(243,235,221,0.14)] text-xs focus:outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-xs text-[#858983] block mb-1 font-mono">Overlap (chars):</label>
            <input
              type="number"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(parseInt(e.target.value) || 80)}
              className="w-full px-3 py-2 bg-[#171A17] text-[#F3EBDD] rounded-xl border border-[rgba(243,235,221,0.14)] text-xs focus:outline-none font-mono"
            />
          </div>
        </div>

        <button
          onClick={handleReindex}
          disabled={isReindexing}
          className="flex items-center space-x-2 px-4 py-2 bg-[#1C563E] hover:bg-[#256F50] text-[#F3EBDD] rounded-xl text-xs font-semibold transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isReindexing ? 'animate-spin' : ''}`} />
          <span>{isReindexing ? 'REINDEXING CORPUS...' : 'REBUILD VECTOR INDEX'}</span>
        </button>
      </div>

      {/* Upload Document */}
      <div className="p-6 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
        <h2 className="text-sm font-semibold text-[#F3EBDD] uppercase tracking-wider font-mono flex items-center space-x-2 mb-3">
          <Upload className="w-4 h-4 text-[#D9C48A]" />
          <span>Upload Custom Document to [{collection.toUpperCase()}]</span>
        </h2>
        <input
          type="file"
          accept=".txt,.pdf,.docx,.md"
          onChange={handleFileUpload}
          className="text-xs text-[#858983] file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-[#171A17] file:text-[#F3EBDD] hover:file:bg-[#1E231E] cursor-pointer"
        />
        {uploadStatus && (
          <p className="mt-2 text-xs text-[#A8D5BA] font-mono">{uploadStatus}</p>
        )}
      </div>

      {/* Document List */}
      <div className="p-6 rounded-2xl bg-[#111311] border border-[rgba(243,235,221,0.12)]">
        <h2 className="text-sm font-semibold text-[#F3EBDD] uppercase tracking-wider font-mono mb-4">
          Indexed Documents in [{collection.toUpperCase()}] ({documents.length})
        </h2>

        {isLoading ? (
          <p className="text-xs text-[#858983]">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-xs text-[#858983]">No documents found in this collection.</p>
        ) : (
          <div className="divide-y divide-[rgba(243,235,221,0.06)] font-mono text-xs">
            {documents.map((doc) => (
              <div key={doc.id} className="py-3 flex items-center justify-between gap-4">
                <div>
                  <span className="font-semibold text-[#F3EBDD]">{doc.name}</span>
                  <span className="ml-2 px-2 py-0.5 rounded text-[9px] bg-[#1C563E]/30 text-[#A8D5BA]">
                    {doc.category_badge}
                  </span>
                  <span className="ml-2 text-[#858983]">({doc.chunks_count} chunks)</span>
                </div>
                {!doc.is_sample && (
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-[#D58A8A] hover:text-[#FF9999] p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
