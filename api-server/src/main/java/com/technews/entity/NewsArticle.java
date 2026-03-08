package com.technews.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "news_articles")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class NewsArticle {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "source_name", nullable = false)
    private String sourceName;

    @Column(name = "source_url", nullable = false, unique = true)
    private String sourceUrl;

    @Column(name = "original_title", nullable = false, columnDefinition = "TEXT")
    private String originalTitle;

    @Column(name = "original_description", columnDefinition = "TEXT")
    private String originalDescription;

    @Column(name = "chinese_title", columnDefinition = "TEXT")
    private String chineseTitle;

    @Column(name = "chinese_summary", columnDefinition = "TEXT")
    private String chineseSummary;

    @Column(name = "full_content", columnDefinition = "TEXT")
    private String fullContent;

    // Scores
    @Column(name = "total_score")
    private Float totalScore;

    @Column(name = "industry_impact_score")
    private Float industryImpactScore;

    @Column(name = "milestone_score")
    private Float milestoneScore;

    @Column(name = "attention_score")
    private Float attentionScore;

    // Timestamps
    @Column(name = "published_at")
    private LocalDateTime publishedAt;

    @Column(name = "processed_at")
    private LocalDateTime processedAt;

    // Reflection
    @Column(name = "reflection_retries")
    private Integer reflectionRetries;

    @Column(name = "reflection_passed")
    private Boolean reflectionPassed;

    @Column(name = "reflection_feedback", columnDefinition = "TEXT")
    private String reflectionFeedback;

    @Column(name = "is_published")
    private Boolean isPublished;

    // Metadata - using native Hibernate 6 JSON support
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata", columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    // DeepSearch Report
    @Column(name = "deepsearch_report", columnDefinition = "TEXT")
    private String deepsearchReport;

    @Column(name = "deepsearch_performed_at")
    private LocalDateTime deepsearchPerformedAt;

    @OneToOne(mappedBy = "article", fetch = FetchType.LAZY)
    private ArticleEmbedding embedding;
}