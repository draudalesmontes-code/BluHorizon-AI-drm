-- enforces roles in chats
ALTER TABLE messages ADD CONSTRAINT chk_role CHECK (role IN ('user','assistant'));

-- prevents duplicate filenames per user
ALTER TABLE documents ADD CONSTRAINT documents_user_filename_unique UNIQUE (user_id, filename);