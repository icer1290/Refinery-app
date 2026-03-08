-- Add deepsearch_report column to news_articles table
ALTER TABLE news_articles
ADD COLUMN deepsearch_report TEXT;

ALTER TABLE news_articles
ADD COLUMN deepsearch_performed_at TIMESTAMP WITH TIME ZONE;