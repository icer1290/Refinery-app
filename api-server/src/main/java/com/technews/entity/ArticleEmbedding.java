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

    @Column(name = "article_id", nullable = false)
    private UUID articleId;

    // Embedding column is vector(1536) type - we handle this via native SQL in VectorSearchRepository
    // This field is not mapped directly as JPA doesn't support pgvector natively
    @Column(name = "content_hash", nullable = false)
    private String contentHash;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    // Chunk-specific fields for RAG (matching ai-engine's schema)
    @Column(name = "chunk_number", nullable = false)
    private Integer chunkNumber;

    @Column(name = "chunk_text", columnDefinition = "TEXT")
    private String chunkText;

    @Column(name = "chunk_start")
    private Integer chunkStart;

    @Column(name = "chunk_end")
    private Integer chunkEnd;

    @Column(name = "embedding_type", nullable = false, length = 20)
    private String embeddingType;

    // Note: We don't map the @OneToOne relationship to NewsArticle here
    // because article_embeddings is actually a one-to-many table (multiple chunks per article).
    // The article_id column is just a foreign key, not a unique constraint.
}