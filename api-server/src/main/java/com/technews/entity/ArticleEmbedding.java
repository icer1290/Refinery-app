package com.technews.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "article_embeddings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleEmbedding {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "article_id", nullable = false, unique = true)
    private UUID articleId;

    // Embedding column is vector(1536) type - we handle this via native SQL in VectorSearchRepository
    // This field is not mapped directly as JPA doesn't support pgvector natively
    @Column(name = "content_hash", nullable = false)
    private String contentHash;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "article_id", insertable = false, updatable = false)
    private NewsArticle article;
}