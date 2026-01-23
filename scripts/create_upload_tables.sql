-- Create tables for uploaded training data
-- This stores parsed content from uploaded files for agent training

-- Main uploaded documents table
CREATE TABLE IF NOT EXISTS uploaded_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash for deduplication
    file_type VARCHAR(50) NOT NULL,  -- txt, md, pdf, docx, etc.
    file_size INTEGER NOT NULL,
    content TEXT NOT NULL,  -- Parsed text content
    content_length INTEGER,
    line_count INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(100),  -- User who uploaded
    processed BOOLEAN DEFAULT TRUE,
    agent_type VARCHAR(50),  -- Target agent: sql, csharp, epicor, general
    category VARCHAR(100),  -- Optional categorization
    tags TEXT[],  -- Array of tags
    metadata JSONB  -- Additional metadata from parsing
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_file_hash ON uploaded_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_file_type ON uploaded_documents(file_type);
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_uploaded_at ON uploaded_documents(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_agent_type ON uploaded_documents(agent_type);
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_category ON uploaded_documents(category);

-- Full-text search index on content
CREATE INDEX IF NOT EXISTS idx_uploaded_docs_content_fts ON uploaded_documents USING gin(to_tsvector('english', content));

-- Document chunks table (for large documents split into chunks)
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES uploaded_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON document_chunks(chunk_index);

-- Upload history/audit log
CREATE TABLE IF NOT EXISTS upload_history (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_size INTEGER,
    status VARCHAR(50) NOT NULL,  -- success, failed, duplicate
    error_message TEXT,
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_upload_history_uploaded_at ON upload_history(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_upload_history_status ON upload_history(status);

-- Comments for documentation
COMMENT ON TABLE uploaded_documents IS 'Stores parsed content from uploaded files for agent training';
COMMENT ON COLUMN uploaded_documents.file_hash IS 'SHA-256 hash for duplicate detection';
COMMENT ON COLUMN uploaded_documents.content IS 'Parsed plain text content from the file';
COMMENT ON COLUMN uploaded_documents.agent_type IS 'Which agent this document is intended for';
COMMENT ON COLUMN uploaded_documents.metadata IS 'JSON metadata extracted during parsing';

COMMENT ON TABLE document_chunks IS 'Large documents split into chunks for processing';
COMMENT ON TABLE upload_history IS 'Audit log of all upload attempts';
