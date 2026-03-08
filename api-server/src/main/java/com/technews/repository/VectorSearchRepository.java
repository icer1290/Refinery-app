package com.technews.repository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class VectorSearchRepository {

    private final EntityManager entityManager;

    public List<SimilarArticleResult> findSimilarArticles(UUID articleId, int limit, double threshold) {
        String sql = """
            SELECT na.id, na.source_name, na.source_url, na.original_title, na.original_description,
                   na.chinese_title, na.chinese_summary, na.full_content,
                   na.total_score, na.industry_impact_score, na.milestone_score, na.attention_score,
                   na.published_at, na.processed_at,
                   1 - (ae.embedding <=> (SELECT embedding FROM article_embeddings WHERE article_id = :articleId)) as similarity
            FROM news_articles na
            JOIN article_embeddings ae ON na.id = ae.article_id
            WHERE na.id != :articleId
              AND 1 - (ae.embedding <=> (SELECT embedding FROM article_embeddings WHERE article_id = :articleId)) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
            """;

        Query query = entityManager.createNativeQuery(sql)
                .setParameter("articleId", articleId)
                .setParameter("threshold", threshold)
                .setParameter("limit", limit);

        @SuppressWarnings("unchecked")
        List<Object[]> results = query.getResultList();

        return results.stream().map(this::mapToResult).toList();
    }

    public List<SimilarArticleResult> findSimilarArticlesByEmbedding(float[] embedding, int limit, double threshold) {
        String embeddingStr = arrayToString(embedding);

        String sql = """
            SELECT na.id, na.source_name, na.source_url, na.original_title, na.original_description,
                   na.chinese_title, na.chinese_summary, na.full_content,
                   na.total_score, na.industry_impact_score, na.milestone_score, na.attention_score,
                   na.published_at, na.processed_at,
                   1 - (ae.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM news_articles na
            JOIN article_embeddings ae ON na.id = ae.article_id
            WHERE 1 - (ae.embedding <=> CAST(:embedding AS vector)) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
            """;

        Query query = entityManager.createNativeQuery(sql)
                .setParameter("embedding", embeddingStr)
                .setParameter("threshold", threshold)
                .setParameter("limit", limit);

        @SuppressWarnings("unchecked")
        List<Object[]> results = query.getResultList();

        return results.stream().map(this::mapToResult).toList();
    }

    private SimilarArticleResult mapToResult(Object[] row) {
        return new SimilarArticleResult(
                UUID.fromString(row[0].toString()),
                (String) row[1],
                (String) row[2],
                (String) row[3],
                (String) row[4],
                (String) row[5],
                (String) row[6],
                (String) row[7],
                row[8] != null ? ((Number) row[8]).floatValue() : null,
                row[9] != null ? ((Number) row[9]).floatValue() : null,
                row[10] != null ? ((Number) row[10]).floatValue() : null,
                row[11] != null ? ((Number) row[11]).floatValue() : null,
                row[12] != null ? ((java.sql.Timestamp) row[12]).toLocalDateTime() : null,
                row[13] != null ? ((java.sql.Timestamp) row[13]).toLocalDateTime() : null,
                ((Number) row[14]).doubleValue()
        );
    }

    private String arrayToString(float[] array) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < array.length; i++) {
            if (i > 0) sb.append(",");
            sb.append(array[i]);
        }
        sb.append("]");
        return sb.toString();
    }

    public static class SimilarArticleResult {
        private final UUID id;
        private final String sourceName;
        private final String sourceUrl;
        private final String originalTitle;
        private final String originalDescription;
        private final String chineseTitle;
        private final String chineseSummary;
        private final String fullContent;
        private final Float totalScore;
        private final Float industryImpactScore;
        private final Float milestoneScore;
        private final Float attentionScore;
        private final LocalDateTime publishedAt;
        private final LocalDateTime processedAt;
        private final Double similarity;

        public SimilarArticleResult(UUID id, String sourceName, String sourceUrl, String originalTitle,
                                    String originalDescription, String chineseTitle, String chineseSummary,
                                    String fullContent, Float totalScore, Float industryImpactScore,
                                    Float milestoneScore, Float attentionScore, LocalDateTime publishedAt,
                                    LocalDateTime processedAt, Double similarity) {
            this.id = id;
            this.sourceName = sourceName;
            this.sourceUrl = sourceUrl;
            this.originalTitle = originalTitle;
            this.originalDescription = originalDescription;
            this.chineseTitle = chineseTitle;
            this.chineseSummary = chineseSummary;
            this.fullContent = fullContent;
            this.totalScore = totalScore;
            this.industryImpactScore = industryImpactScore;
            this.milestoneScore = milestoneScore;
            this.attentionScore = attentionScore;
            this.publishedAt = publishedAt;
            this.processedAt = processedAt;
            this.similarity = similarity;
        }

        public UUID getId() { return id; }
        public String getSourceName() { return sourceName; }
        public String getSourceUrl() { return sourceUrl; }
        public String getOriginalTitle() { return originalTitle; }
        public String getOriginalDescription() { return originalDescription; }
        public String getChineseTitle() { return chineseTitle; }
        public String getChineseSummary() { return chineseSummary; }
        public String getFullContent() { return fullContent; }
        public Float getTotalScore() { return totalScore; }
        public Float getIndustryImpactScore() { return industryImpactScore; }
        public Float getMilestoneScore() { return milestoneScore; }
        public Float getAttentionScore() { return attentionScore; }
        public LocalDateTime getPublishedAt() { return publishedAt; }
        public LocalDateTime getProcessedAt() { return processedAt; }
        public Double getSimilarity() { return similarity; }
    }
}