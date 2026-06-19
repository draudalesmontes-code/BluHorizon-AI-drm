-- Seed data for BluHorizon development/learning

-- Users
INSERT INTO users (email, password_hash) VALUES
('diego@bluhorizon.ai', 'hashed_pw_1'),
('ana@bluhorizon.ai',   'hashed_pw_2');

-- Documents (user 1 has 3, user 2 has 2)
INSERT INTO documents (user_id, filename, file_type) VALUES
(1, 'project_proposal.pdf',    'pdf'),
(1, 'meeting_notes.docx',      'docx'),
(1, 'financial_report.xlsx',   'xlsx'),
(2, 'research_paper.pdf',      'pdf'),
(2, 'onboarding_guide.docx',   'docx');

-- Chunks (2-3 per document)
INSERT INTO chunks (document_id, chunk_text, source) VALUES
(1, 'The project aims to build an AI-powered document management system.', 'project_proposal.pdf'),
(1, 'Phase one will focus on document ingestion and vector search capabilities.', 'project_proposal.pdf'),
(2, 'Meeting agenda: Q3 roadmap, hiring plan, infrastructure costs.', 'meeting_notes.docx'),
(2, 'Decision: migrate from SQLite to PostgreSQL by end of Q3.', 'meeting_notes.docx'),
(2, 'Action items: Diego to finalize schema, Ana to set up CI pipeline.', 'meeting_notes.docx'),
(3, 'Total revenue for Q2: $240,000. Operating costs: $180,000.', 'financial_report.xlsx'),
(4, 'Large language models have transformed natural language processing tasks.', 'research_paper.pdf'),
(4, 'RAG systems combine retrieval mechanisms with generative models.', 'research_paper.pdf'),
(4, 'Embedding models convert text into dense vector representations.', 'research_paper.pdf'),
(5, 'Welcome to BluHorizon. This guide covers your first week.', 'onboarding_guide.docx'),
(5, 'Your AI assistant can answer questions about any uploaded document.', 'onboarding_guide.docx');

-- Conversations
INSERT INTO conversations (user_id, title) VALUES
(1, 'Q3 Planning Discussion'),
(1, 'Financial Report Review'),
(2, 'Research Paper Summary');

-- Messages
INSERT INTO messages (conversation_id, role, content) VALUES
(1, 'user',      'What were the action items from the meeting notes?'),
(1, 'assistant', 'Based on the meeting notes, the action items are: Diego to finalize the schema and Ana to set up the CI pipeline.'),
(1, 'user',      'What is the deadline for the PostgreSQL migration?'),
(1, 'assistant', 'The notes mention the migration should be completed by end of Q3.'),
(2, 'user',      'Summarize the financial report.'),
(2, 'assistant', 'Q2 revenue was $240,000 with operating costs of $180,000, leaving a gross margin of $60,000.'),
(3, 'user',      'What does the paper say about RAG systems?'),
(3, 'assistant', 'The paper states that RAG systems combine retrieval mechanisms with generative models to improve answer accuracy.'),
(3, 'user',      'How are embeddings described?'),
(3, 'assistant', 'Embeddings are described as dense vector representations of text produced by embedding models.');
