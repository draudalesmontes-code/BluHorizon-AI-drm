--(Users -> documents)
CREATE INDEX idx_documents_user_id ON documents(user_id);

--(documents -> chunks)
CREATE INDEX idx_chunks_document_id ON chunks(document_id);

--conversations.user_id
CREATE INDEX idx_conversation_user_id ON conversations(user_id);

--most queried - every chat history fetch hits this
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

