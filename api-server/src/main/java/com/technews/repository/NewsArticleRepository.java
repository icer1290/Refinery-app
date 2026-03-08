package com.technews.repository;

import com.technews.entity.NewsArticle;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface NewsArticleRepository extends JpaRepository<NewsArticle, UUID> {

    List<NewsArticle> findByPublishedAtBetweenOrderByPublishedAtDescTotalScoreDesc(
            LocalDateTime start, LocalDateTime end);

    List<NewsArticle> findByPublishedAtAfterOrderByPublishedAtDescTotalScoreDesc(LocalDateTime publishedAt);

    @Query("SELECT DISTINCT DATE(n.publishedAt) FROM NewsArticle n WHERE n.publishedAt IS NOT NULL ORDER BY DATE(n.publishedAt) DESC")
    List<java.time.LocalDate> findDistinctPublishedDates();

    @Query("SELECT n FROM NewsArticle n WHERE n.publishedAt >= :start AND n.publishedAt < :end ORDER BY n.publishedAt DESC, n.totalScore DESC")
    List<NewsArticle> findTodayNews(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);
}