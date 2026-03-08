package com.technews.repository;

import com.technews.entity.ArticleEmbedding;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ArticleEmbeddingRepository extends JpaRepository<ArticleEmbedding, UUID> {

    Optional<ArticleEmbedding> findByArticleId(UUID articleId);

    void deleteByArticleId(UUID articleId);
}